# 퀴즈 관련 Pydantic 스키마
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class QuizCreate(BaseModel):
    """문제 생성 요청 스키마"""
    subject: str = Field(..., example="수학", description="과목명")
    topic: str = Field(..., example="이차방정식", description="학습 주제")
    difficulty: str = Field(default="medium", pattern="^(easy|medium|hard)$", description="난이도")
    count: int = Field(default=5, ge=1, le=20, description="생성할 문제 수")


class QuizResponse(BaseModel):
    """문제 응답 스키마 (보기 포함, 정답 미포함)"""
    id: int
    subject: str
    topic: str
    difficulty: str
    question: str
    options: dict  # {"A": "...", "B": "...", "C": "...", "D": "..."}
    created_at: datetime

    model_config = {"from_attributes": True}


class QuizDetail(BaseModel):
    """문제 상세 스키마 (정답 + 해설 포함, 채점 후 반환용)"""
    id: int
    subject: str
    topic: str
    difficulty: str
    question: str
    options: dict
    correct_answer: str
    explanation: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class QuizSubmit(BaseModel):
    """문제 답안 제출 스키마"""
    quiz_id: int = Field(..., description="퀴즈 ID")
    user_answer: str = Field(..., description="사용자 선택 답 키 (A/B/C/D)")


class QuizResult(BaseModel):
    """채점 결과 스키마"""
    quiz_id: int
    is_correct: bool
    correct_answer: str
    user_answer: str
    explanation: Optional[str] = None
    message: str  # "정답입니다!" / "오답입니다. 다시 도전해보세요!"


class WrongQuizResponse(BaseModel):
    """오답 문제 목록 응답 스키마"""
    quiz: QuizDetail
    wrong_count: int          # 해당 문제를 틀린 횟수
    last_attempted_at: datetime
