# 퀴즈 라우터 - 문제 생성, 답안 제출, 오답 조회
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.attempt import QuizAttempt
from app.models.quiz import Quiz
from app.models.study_session import StudySession
from app.models.user import User, SubscriptionPlan
from app.routers.users import get_current_user
from app.schemas.quiz import (
    QuizCreate,
    QuizDetail,
    QuizResponse,
    QuizResult,
    QuizSubmit,
)
from app.services.analytics import get_wrong_quizzes
from app.services.quiz_generator import analyze_wrong_answers, generate_quizzes, grade_answer

router = APIRouter(prefix="/quiz", tags=["quiz"])

# 무료 플랜 일일 문제 생성 제한
FREE_PLAN_DAILY_LIMIT = 10


# ── 엔드포인트 ───────────────────────────────────────────────

@router.post("/generate", response_model=list[QuizResponse], status_code=status.HTTP_201_CREATED)
async def create_quizzes(
    quiz_in: QuizCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """
    Gemini API로 퀴즈 문제를 생성한다.
    - 무료 플랜: 일 10문제 제한
    - 베이직/프로 플랜: 무제한
    """
    # 무료 플랜 일일 제한 확인
    if current_user.subscription_plan == SubscriptionPlan.FREE.value:
        from datetime import datetime, date
        today_start = datetime.combine(date.today(), datetime.min.time())
        result = await db.execute(
            select(Quiz).where(
                Quiz.user_id == current_user.id,
                Quiz.created_at >= today_start,
            )
        )
        today_quizzes = result.scalars().all()
        if len(today_quizzes) + quiz_in.count > FREE_PLAN_DAILY_LIMIT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"무료 플랜은 하루 {FREE_PLAN_DAILY_LIMIT}문제까지 생성할 수 있습니다. 구독을 업그레이드하세요.",
            )

    # Gemini API로 문제 생성
    try:
        raw_quizzes = await generate_quizzes(
            subject=quiz_in.subject,
            topic=quiz_in.topic,
            difficulty=quiz_in.difficulty,
            count=quiz_in.count,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"문제 생성 중 오류가 발생했습니다: {str(e)}",
        )

    # DB에 저장
    created = []
    for q in raw_quizzes:
        quiz = Quiz(
            subject=quiz_in.subject,
            topic=quiz_in.topic,
            difficulty=quiz_in.difficulty,
            question=q["question"],
            options=q["options"],
            correct_answer=q["correct_answer"],
            explanation=q.get("explanation", ""),
            user_id=current_user.id,
        )
        db.add(quiz)
        await db.flush()
        await db.refresh(quiz)
        created.append(quiz)

    return created


@router.post("/submit", response_model=QuizResult)
async def submit_answer(
    submit: QuizSubmit,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """
    답안을 제출하고 채점 결과를 반환한다.
    오답 시 해설과 피드백을 포함한다.
    """
    # 문제 조회
    result = await db.execute(select(Quiz).where(Quiz.id == submit.quiz_id))
    quiz = result.scalar_one_or_none()
    if quiz is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="문제를 찾을 수 없습니다.")

    # 채점
    grade = await grade_answer(
        question=quiz.question,
        options=quiz.options,
        correct_answer=quiz.correct_answer,
        user_answer=submit.user_answer,
        explanation=quiz.explanation or "",
    )

    # 시도 기록 저장
    attempt = QuizAttempt(
        quiz_id=quiz.id,
        user_id=current_user.id,
        user_answer=submit.user_answer.upper(),
        is_correct=grade["is_correct"],
    )
    db.add(attempt)
    await db.flush()

    return QuizResult(
        quiz_id=quiz.id,
        is_correct=grade["is_correct"],
        correct_answer=quiz.correct_answer,
        user_answer=submit.user_answer.upper(),
        explanation=quiz.explanation,
        message="정답입니다!" if grade["is_correct"] else "오답입니다. 다시 도전해보세요!",
    )


@router.get("/wrong", response_model=list[dict])
async def get_wrong_quiz_list(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    subject: Optional[str] = Query(None, description="과목으로 필터링"),
    limit: int = Query(20, ge=1, le=100),
):
    """
    사용자의 오답 문제 목록을 반환한다.
    틀린 횟수가 많은 순으로 정렬된다.
    """
    wrong = await get_wrong_quizzes(db, current_user.id, subject=subject, limit=limit)
    return wrong


@router.get("/wrong/analysis")
async def analyze_wrong(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    subject: Optional[str] = Query(None, description="분석할 과목"),
):
    """
    오답 문제를 Gemini AI로 분석하여 취약점과 학습 방향을 제시한다.
    프로 플랜 전용 기능.
    """
    if current_user.subscription_plan == SubscriptionPlan.FREE.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="AI 오답 분석은 베이직 이상 플랜에서 사용할 수 있습니다.",
        )

    wrong = await get_wrong_quizzes(db, current_user.id, subject=subject, limit=10)
    if not wrong:
        return {"analysis": "오답이 없습니다. 훌륭합니다!", "subject": subject or "전체"}

    # Gemini API 분석 요청용 포맷 변환
    wrong_for_analysis = [
        {
            "question": w["quiz"]["question"],
            "correct_answer": w["quiz"]["correct_answer"],
            "user_answer": "틀림",  # 실제 답은 attempts에서 가져올 수 있으나 요약 분석용
            "explanation": w["quiz"].get("explanation", ""),
        }
        for w in wrong
    ]

    try:
        analysis = await analyze_wrong_answers(
            wrong_quizzes=wrong_for_analysis,
            subject=subject or "전체",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI 분석 중 오류가 발생했습니다: {str(e)}",
        )

    return {"analysis": analysis, "subject": subject or "전체", "wrong_count": len(wrong)}


@router.post("/session/complete")
async def complete_session(
    subject: str,
    quiz_ids: list[int],
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """
    학습 세션을 완료하고 결과를 저장한다.
    제출된 quiz_ids의 시도 기록을 기반으로 점수를 계산한다.
    """
    if not quiz_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="quiz_ids가 비어있습니다.")

    # 해당 세션의 시도 기록 조회 (가장 최근 시도만)
    result = await db.execute(
        select(QuizAttempt).where(
            QuizAttempt.user_id == current_user.id,
            QuizAttempt.quiz_id.in_(quiz_ids),
        )
    )
    attempts = result.scalars().all()

    # quiz_id별 최신 시도만 추출
    latest: dict[int, QuizAttempt] = {}
    for attempt in sorted(attempts, key=lambda a: a.attempted_at):
        latest[attempt.quiz_id] = attempt

    total = len(quiz_ids)
    correct = sum(1 for a in latest.values() if a.is_correct)
    score = round(correct / total * 100, 1) if total > 0 else 0.0

    # 세션 저장
    session = StudySession(
        user_id=current_user.id,
        subject=subject,
        total_questions=total,
        correct_count=correct,
        score=score,
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)

    return {
        "session_id": session.id,
        "subject": subject,
        "total_questions": total,
        "correct_count": correct,
        "wrong_count": total - correct,
        "score": score,
        "message": f"학습 완료! {score}점을 획득했습니다.",
    }


@router.get("/{quiz_id}", response_model=QuizDetail)
async def get_quiz(
    quiz_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """특정 퀴즈 상세 조회 (정답 포함)"""
    result = await db.execute(
        select(Quiz).where(Quiz.id == quiz_id, Quiz.user_id == current_user.id)
    )
    quiz = result.scalar_one_or_none()
    if quiz is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="문제를 찾을 수 없습니다.")
    return quiz
