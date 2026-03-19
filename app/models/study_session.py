# 학습 세션 모델 - 한 번의 퀴즈 세션 결과를 저장
from datetime import datetime
from sqlalchemy import Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class StudySession(Base):
    __tablename__ = "study_sessions"

    # 기본 필드
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # 소유자
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)

    # 세션 메타 정보
    subject: Mapped[str] = mapped_column(String(100), nullable=False)       # 학습 과목

    # 결과 요약
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False)   # 총 문제 수
    correct_count: Mapped[int] = mapped_column(Integer, nullable=False)     # 맞힌 문제 수
    score: Mapped[float] = mapped_column(Float, nullable=False)             # 점수 (0.0 ~ 100.0)

    # 타임스탬프
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 관계
    user: Mapped["User"] = relationship("User", back_populates="study_sessions")

    @property
    def wrong_count(self) -> int:
        """오답 수"""
        return self.total_questions - self.correct_count

    def __repr__(self) -> str:
        return f"<StudySession id={self.id} subject={self.subject} score={self.score}>"
