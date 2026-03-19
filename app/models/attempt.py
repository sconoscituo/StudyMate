# 퀴즈 풀이 시도 모델
from datetime import datetime
from sqlalchemy import Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    # 기본 필드
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # 외래키
    quiz_id: Mapped[int] = mapped_column(Integer, ForeignKey("quizzes.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)

    # 답안 정보
    user_answer: Mapped[str] = mapped_column(String(10), nullable=False)   # 사용자가 선택한 답 키 (예: "B")
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)       # 정오답 여부

    # 타임스탬프
    attempted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 관계
    quiz: Mapped["Quiz"] = relationship("Quiz", back_populates="attempts")
    user: Mapped["User"] = relationship("User", back_populates="attempts")

    def __repr__(self) -> str:
        return f"<QuizAttempt id={self.id} quiz_id={self.quiz_id} correct={self.is_correct}>"
