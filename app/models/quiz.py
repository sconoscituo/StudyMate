# 퀴즈(문제) 모델
from datetime import datetime
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Quiz(Base):
    __tablename__ = "quizzes"

    # 기본 필드
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # 문제 메타 정보
    subject: Mapped[str] = mapped_column(String(100), nullable=False)   # 과목 (예: 수학, 영어, 한국사)
    topic: Mapped[str] = mapped_column(String(200), nullable=False)      # 주제 (예: 미분적분, 관계대명사)
    difficulty: Mapped[str] = mapped_column(String(20), default="medium") # 난이도: easy / medium / hard

    # 문제 본문
    question: Mapped[str] = mapped_column(Text, nullable=False)          # 문제 텍스트
    options: Mapped[dict] = mapped_column(JSON, nullable=False)           # 보기 목록 {"A": "...", "B": "...", ...}
    correct_answer: Mapped[str] = mapped_column(String(10), nullable=False)  # 정답 키 (예: "A")
    explanation: Mapped[str] = mapped_column(Text, nullable=True)         # 해설

    # 소유자
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)

    # 타임스탬프
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 관계
    user: Mapped["User"] = relationship("User", back_populates="quizzes")
    attempts: Mapped[list["QuizAttempt"]] = relationship("QuizAttempt", back_populates="quiz", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Quiz id={self.id} subject={self.subject} topic={self.topic}>"
