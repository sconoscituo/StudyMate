# Gemini API를 활용한 퀴즈 생성, 채점, 오답 분석 서비스
import json
import re
from typing import Optional

import google.generativeai as genai

from app.config import settings

# Gemini API 초기화
genai.configure(api_key=settings.gemini_api_key)


def _get_model() -> genai.GenerativeModel:
    """Gemini 모델 인스턴스 반환"""
    return genai.GenerativeModel("gemini-pro")


async def generate_quizzes(
    subject: str,
    topic: str,
    difficulty: str,
    count: int,
) -> list[dict]:
    """
    Gemini API로 과목/주제별 객관식 문제를 생성한다.

    Returns:
        list of dict: [
            {
                "question": "...",
                "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
                "correct_answer": "A",
                "explanation": "..."
            },
            ...
        ]
    """
    difficulty_map = {
        "easy": "쉬운 (기초 개념 확인)",
        "medium": "중간 (응용 이해)",
        "hard": "어려운 (심화 분석)",
    }
    difficulty_label = difficulty_map.get(difficulty, "중간")

    prompt = f"""
당신은 교육 전문가입니다. 아래 조건에 맞는 객관식 문제를 {count}개 생성해주세요.

과목: {subject}
주제: {topic}
난이도: {difficulty_label}

각 문제는 반드시 아래 JSON 배열 형식으로만 응답해주세요. 다른 텍스트는 포함하지 마세요.

[
  {{
    "question": "문제 텍스트",
    "options": {{
      "A": "보기 A",
      "B": "보기 B",
      "C": "보기 C",
      "D": "보기 D"
    }},
    "correct_answer": "A",
    "explanation": "정답 해설 (왜 A가 정답인지 간략히)"
  }}
]

요구사항:
- 각 문제는 명확하고 교육적이어야 합니다
- 오답 보기도 그럴듯하게 만들어주세요
- 해설은 학습에 도움이 되도록 상세히 작성해주세요
- 반드시 유효한 JSON만 응답하세요
"""

    model = _get_model()
    response = model.generate_content(prompt)
    raw_text = response.text.strip()

    # JSON 블록 추출 (```json ... ``` 형식 처리)
    json_match = re.search(r"\[.*\]", raw_text, re.DOTALL)
    if not json_match:
        raise ValueError(f"Gemini 응답에서 JSON을 파싱할 수 없습니다: {raw_text[:200]}")

    quizzes = json.loads(json_match.group())

    # 필드 유효성 검증
    required_keys = {"question", "options", "correct_answer", "explanation"}
    for i, quiz in enumerate(quizzes):
        missing = required_keys - set(quiz.keys())
        if missing:
            raise ValueError(f"문제 {i+1}에 필수 필드 누락: {missing}")

    return quizzes


async def analyze_wrong_answers(
    wrong_quizzes: list[dict],
    subject: str,
) -> str:
    """
    오답 목록을 바탕으로 Gemini API에 취약점 분석 및 학습 방향을 요청한다.

    Args:
        wrong_quizzes: [{"question": "...", "correct_answer": "...", "user_answer": "...", "explanation": "..."}, ...]
        subject: 과목명

    Returns:
        str: 분석 결과 텍스트
    """
    if not wrong_quizzes:
        return "오답이 없습니다. 훌륭합니다!"

    wrong_summary = "\n".join(
        f"- 문제: {q['question']}\n  정답: {q['correct_answer']} / 내 답: {q['user_answer']}"
        for q in wrong_quizzes[:10]  # 최대 10개만 분석
    )

    prompt = f"""
당신은 학습 코치입니다. 아래는 학생이 {subject} 과목에서 틀린 문제 목록입니다.

{wrong_summary}

위 오답을 분석하여 다음을 한국어로 작성해주세요:
1. 취약한 개념 또는 유형 파악
2. 자주 틀리는 패턴
3. 개선을 위한 구체적인 학습 방법 3가지
4. 다음 학습 추천 주제

500자 이내로 간결하게 작성해주세요.
"""

    model = _get_model()
    response = model.generate_content(prompt)
    return response.text.strip()


async def grade_answer(
    question: str,
    options: dict,
    correct_answer: str,
    user_answer: str,
    explanation: str,
) -> dict:
    """
    사용자 답안을 채점하고 결과를 반환한다.
    (단순 비교 채점 + 오답 시 Gemini 보충 설명 생성 옵션)

    Returns:
        dict: {"is_correct": bool, "feedback": str}
    """
    is_correct = user_answer.upper() == correct_answer.upper()

    if is_correct:
        feedback = "정답입니다! 잘 하셨습니다."
    else:
        # 오답 시 선택한 보기와 정답 보기를 비교하는 피드백
        user_option_text = options.get(user_answer.upper(), "알 수 없음")
        correct_option_text = options.get(correct_answer.upper(), "알 수 없음")
        feedback = (
            f"오답입니다.\n"
            f"선택한 답: {user_answer} - {user_option_text}\n"
            f"정답: {correct_answer} - {correct_option_text}\n"
            f"해설: {explanation}"
        )

    return {"is_correct": is_correct, "feedback": feedback}
