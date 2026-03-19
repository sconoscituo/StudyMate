# 학습 통계 분석 서비스 - 취약점 파악, 개선 방향 제시
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.study_session import StudySession
from app.models.attempt import QuizAttempt
from app.models.quiz import Quiz


async def get_user_study_stats(db: AsyncSession, user_id: int) -> dict:
    """
    사용자의 전체 학습 통계를 계산하여 반환한다.

    Returns:
        dict: {
            "total_sessions": int,
            "total_questions": int,
            "total_correct": int,
            "average_score": float,
            "subject_stats": [...],
            "weak_subjects": [...],
            "recent_sessions": [...]
        }
    """
    # 전체 세션 조회
    sessions_result = await db.execute(
        select(StudySession).where(StudySession.user_id == user_id)
    )
    sessions = sessions_result.scalars().all()

    if not sessions:
        return {
            "total_sessions": 0,
            "total_questions": 0,
            "total_correct": 0,
            "average_score": 0.0,
            "subject_stats": [],
            "weak_subjects": [],
            "recent_sessions": [],
        }

    # 전체 합계 계산
    total_sessions = len(sessions)
    total_questions = sum(s.total_questions for s in sessions)
    total_correct = sum(s.correct_count for s in sessions)
    average_score = round(
        sum(s.score for s in sessions) / total_sessions, 1
    ) if total_sessions > 0 else 0.0

    # 과목별 통계 집계
    subject_data: dict[str, dict] = defaultdict(
        lambda: {"total": 0, "correct": 0, "sessions": 0}
    )
    for s in sessions:
        subject_data[s.subject]["total"] += s.total_questions
        subject_data[s.subject]["correct"] += s.correct_count
        subject_data[s.subject]["sessions"] += 1

    subject_stats = []
    for subject, data in subject_data.items():
        score = round(data["correct"] / data["total"] * 100, 1) if data["total"] > 0 else 0.0
        subject_stats.append({
            "subject": subject,
            "total_questions": data["total"],
            "correct_count": data["correct"],
            "score": score,
            "sessions": data["sessions"],
        })

    # 점수 기준 정렬
    subject_stats.sort(key=lambda x: x["score"])

    # 취약 과목: 점수 60점 미만 과목
    weak_subjects = [s["subject"] for s in subject_stats if s["score"] < 60.0]

    # 최근 5개 세션
    recent = sorted(sessions, key=lambda s: s.created_at, reverse=True)[:5]
    recent_sessions = [
        {
            "id": s.id,
            "subject": s.subject,
            "total_questions": s.total_questions,
            "correct_count": s.correct_count,
            "score": s.score,
            "created_at": s.created_at.isoformat(),
        }
        for s in recent
    ]

    return {
        "total_sessions": total_sessions,
        "total_questions": total_questions,
        "total_correct": total_correct,
        "average_score": average_score,
        "subject_stats": subject_stats,
        "weak_subjects": weak_subjects,
        "recent_sessions": recent_sessions,
    }


async def get_wrong_quizzes(
    db: AsyncSession,
    user_id: int,
    subject: Optional[str] = None,
    limit: int = 20,
) -> list[dict]:
    """
    사용자의 오답 문제 목록을 반환한다.

    Args:
        db: DB 세션
        user_id: 사용자 ID
        subject: 특정 과목 필터 (None이면 전체)
        limit: 최대 반환 수

    Returns:
        list of dict: 오답 문제 정보 + 틀린 횟수
    """
    # 오답만 필터링
    stmt = (
        select(
            QuizAttempt.quiz_id,
            func.count(QuizAttempt.id).label("wrong_count"),
            func.max(QuizAttempt.attempted_at).label("last_attempted_at"),
        )
        .where(
            QuizAttempt.user_id == user_id,
            QuizAttempt.is_correct == False,  # noqa: E712
        )
        .group_by(QuizAttempt.quiz_id)
        .order_by(func.count(QuizAttempt.id).desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.all()

    if not rows:
        return []

    # 퀴즈 상세 정보 조회
    quiz_ids = [row.quiz_id for row in rows]
    quizzes_result = await db.execute(
        select(Quiz).where(Quiz.id.in_(quiz_ids))
    )
    quizzes_map = {q.id: q for q in quizzes_result.scalars().all()}

    wrong_list = []
    for row in rows:
        quiz = quizzes_map.get(row.quiz_id)
        if quiz is None:
            continue
        # 과목 필터 적용
        if subject and quiz.subject != subject:
            continue
        wrong_list.append({
            "quiz": {
                "id": quiz.id,
                "subject": quiz.subject,
                "topic": quiz.topic,
                "difficulty": quiz.difficulty,
                "question": quiz.question,
                "options": quiz.options,
                "correct_answer": quiz.correct_answer,
                "explanation": quiz.explanation,
                "created_at": quiz.created_at.isoformat(),
            },
            "wrong_count": row.wrong_count,
            "last_attempted_at": row.last_attempted_at.isoformat(),
        })

    return wrong_list


def suggest_study_plan(subject_stats: list[dict]) -> list[str]:
    """
    과목별 통계를 기반으로 학습 계획 제안 메시지를 반환한다.

    Returns:
        list[str]: 학습 추천 메시지 목록
    """
    suggestions = []
    for stat in subject_stats:
        score = stat["score"]
        subject = stat["subject"]
        if score < 40:
            suggestions.append(
                f"{subject}: 기초 개념부터 다시 시작하세요. 점수 {score}점 - 집중 보완이 필요합니다."
            )
        elif score < 60:
            suggestions.append(
                f"{subject}: 핵심 개념을 반복 학습하세요. 점수 {score}점 - 오답 문제 복습을 권장합니다."
            )
        elif score < 80:
            suggestions.append(
                f"{subject}: 응용 문제에 도전해보세요. 점수 {score}점 - 심화 주제로 확장하세요."
            )
        else:
            suggestions.append(
                f"{subject}: 우수한 성취도입니다! 점수 {score}점 - 다른 과목도 도전해보세요."
            )
    return suggestions
