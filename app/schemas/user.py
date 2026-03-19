# 사용자 관련 Pydantic 스키마
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """회원가입 요청 스키마"""
    email: EmailStr = Field(..., example="user@example.com")
    password: str = Field(..., min_length=8, example="password123", description="최소 8자 이상")


class UserResponse(BaseModel):
    """사용자 응답 스키마 (비밀번호 제외)"""
    id: int
    email: str
    subscription_plan: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    """JWT 토큰 응답 스키마"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """JWT 페이로드 스키마"""
    email: Optional[str] = None


class LoginRequest(BaseModel):
    """로그인 요청 스키마"""
    email: EmailStr
    password: str


class StudyStats(BaseModel):
    """학습 통계 응답 스키마"""
    total_sessions: int                     # 총 학습 세션 수
    total_questions: int                    # 총 풀이 문제 수
    total_correct: int                      # 총 정답 수
    average_score: float                    # 평균 점수
    subject_stats: list[dict]              # 과목별 통계 [{"subject": "수학", "score": 85.0, ...}]
    weak_subjects: list[str]               # 취약 과목 목록
    recent_sessions: list[dict]            # 최근 5개 세션
