# 사용자 모델
from datetime import datetime
from sqlalchemy import Integer, String, Boolean, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.database import Base


class SubscriptionPlan(str, enum.Enum):
    """구독 플랜 종류"""
    FREE = "free"          # 무료 (일일 문제 생성 제한)
    BASIC = "basic"        # 베이직 월 9,900원
    PRO = "pro"            # 프로 월 19,900원 (무제한 + 심층 분석)


class User(Base):
    __tablename__ = "users"

    # 기본 필드
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # 구독 정보
    subscription_plan: Mapped[str] = mapped_column(
        String(20),
        default=SubscriptionPlan.FREE.value,
        nullable=False
    )

    # 상태
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # 타임스탬프
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 관계
    quizzes: Mapped[list["Quiz"]] = relationship("Quiz", back_populates="user", lazy="selectin")
    attempts: Mapped[list["QuizAttempt"]] = relationship("QuizAttempt", back_populates="user", lazy="selectin")
    study_sessions: Mapped[list["StudySession"]] = relationship("StudySession", back_populates="user", lazy="selectin")

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} plan={self.subscription_plan}>"
