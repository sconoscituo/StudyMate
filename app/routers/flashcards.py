"""
AI 플래시카드 생성 + 간격 반복 학습 라우터
"""
import json
import google.generativeai as genai
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional
from app.database import get_db
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/flashcards", tags=["플래시카드"])

try:
    from app.config import config
    GEMINI_KEY = config.GEMINI_API_KEY
except Exception:
    GEMINI_KEY = ""


class FlashcardGenerateRequest(BaseModel):
    content: str          # 학습 내용 (텍스트)
    subject: Optional[str] = None
    count: int = 10
    difficulty: Optional[str] = "중간"  # 쉬움, 중간, 어려움


class Flashcard(BaseModel):
    front: str   # 질문
    back: str    # 답변
    hint: Optional[str] = None


class FlashcardSet(BaseModel):
    subject: Optional[str]
    cards: List[Flashcard]
    total: int


@router.post("/generate", response_model=FlashcardSet)
async def generate_flashcards(
    request: FlashcardGenerateRequest,
    current_user: User = Depends(get_current_user),
):
    """학습 내용에서 AI 플래시카드 자동 생성"""
    if not GEMINI_KEY:
        raise HTTPException(500, "AI 서비스 설정이 필요합니다")

    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")

    prompt = f"""다음 내용을 바탕으로 {request.difficulty} 난이도의 플래시카드 {request.count}개를 만들어줘.

과목: {request.subject or '일반'}
내용:
{request.content[:2000]}

JSON 배열로 반환 (마크다운 없이):
[
  {{
    "front": "질문",
    "back": "답변 (간결하게)",
    "hint": "힌트 (선택사항, 없으면 null)"
  }}
]"""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```"):
            text = text[text.find("["):text.rfind("]") + 1]
        cards_data = json.loads(text)
        cards = [Flashcard(**c) for c in cards_data[:request.count]]
        return FlashcardSet(subject=request.subject, cards=cards, total=len(cards))
    except Exception:
        raise HTTPException(500, "플래시카드 생성 중 오류가 발생했습니다")


@router.post("/spaced-repetition")
async def get_review_schedule(
    known_count: int,
    unknown_count: int,
    current_user: User = Depends(get_current_user),
):
    """간격 반복 학습 스케줄 계산 (SM-2 알고리즘 기반)"""
    total = known_count + unknown_count
    if total == 0:
        return {"next_review": "오늘", "interval_days": 1}

    retention_rate = known_count / total
    if retention_rate >= 0.9:
        interval = 7
        message = "훌륭해요! 1주일 후 복습하세요"
    elif retention_rate >= 0.7:
        interval = 3
        message = "잘 하고 있어요! 3일 후 복습하세요"
    elif retention_rate >= 0.5:
        interval = 1
        message = "내일 다시 복습하세요"
    else:
        interval = 0
        message = "오늘 한 번 더 복습하세요"

    return {
        "retention_rate": round(retention_rate * 100, 1),
        "interval_days": interval,
        "message": message,
        "known": known_count,
        "unknown": unknown_count,
    }
