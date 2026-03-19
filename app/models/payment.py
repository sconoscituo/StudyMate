# 결제 모델 - 포트원(PortOne) 결제 내역 저장
from datetime import datetime
from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
import enum

from app.database import Base


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    CANCELLED = "cancelled"
    FAILED = "failed"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    imp_uid: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)  # 포트원 결제 고유번호
    merchant_uid: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)  # 주문번호
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)  # 결제금액 (원)
    plan: Mapped[str] = mapped_column(String(20), nullable=False)  # free / basic / premium
    status: Mapped[str] = mapped_column(String(20), default=PaymentStatus.PENDING.value, nullable=False)
    cancel_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<Payment id={self.id} imp_uid={self.imp_uid} plan={self.plan} status={self.status}>"
