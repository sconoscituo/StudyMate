# 결제 라우터 - 포트원 결제 검증/취소/내역 조회
# 구독 플랜: FREE(무료), BASIC(월 9,900원), PREMIUM(월 19,900원)
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.models.payment import Payment, PaymentStatus
from app.models.user import User
from app.services.payment import verify_payment, cancel_payment, PLAN_PRICES
from app.routers.users import get_current_user

router = APIRouter(prefix="/payments", tags=["payments"])


# ── 스키마 ────────────────────────────────────────────────────

class PaymentVerifyRequest(BaseModel):
    imp_uid: str
    merchant_uid: str
    plan: str  # basic / premium


class PaymentCancelRequest(BaseModel):
    imp_uid: str
    reason: str = "사용자 요청 취소"


# ── 라우터 ────────────────────────────────────────────────────

@router.post("/verify", summary="결제 검증 후 구독 업그레이드")
async def verify_and_upgrade(
    body: PaymentVerifyRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """
    포트원 결제 검증 후 구독 플랜을 업그레이드합니다.
    클라이언트에서 결제 완료 후 imp_uid, merchant_uid를 전달하면
    서버에서 금액 위변조 여부를 검증합니다.
    """
    expected_amount = PLAN_PRICES.get(body.plan)
    if expected_amount is None or expected_amount == 0:
        raise HTTPException(status_code=400, detail=f"유효하지 않은 플랜입니다: {body.plan}")

    # 중복 결제 확인
    result = await db.execute(
        select(Payment).where(Payment.imp_uid == body.imp_uid)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="이미 처리된 결제입니다.")

    # 포트원 결제 검증
    is_valid = await verify_payment(body.imp_uid, expected_amount)
    if not is_valid:
        payment = Payment(
            imp_uid=body.imp_uid,
            merchant_uid=body.merchant_uid,
            user_id=current_user.id,
            amount=expected_amount,
            plan=body.plan,
            status=PaymentStatus.FAILED.value,
        )
        db.add(payment)
        await db.commit()
        raise HTTPException(status_code=400, detail="결제 검증 실패: 금액이 일치하지 않습니다.")

    # 결제 내역 저장
    payment = Payment(
        imp_uid=body.imp_uid,
        merchant_uid=body.merchant_uid,
        user_id=current_user.id,
        amount=expected_amount,
        plan=body.plan,
        status=PaymentStatus.PAID.value,
    )
    db.add(payment)

    # 구독 플랜 업그레이드
    current_user.subscription_plan = body.plan
    await db.commit()

    return {"message": "결제 검증 완료. 구독이 업그레이드되었습니다.", "plan": body.plan, "amount": expected_amount}


@router.post("/cancel", summary="구독 취소 및 환불")
async def cancel_subscription(
    body: PaymentCancelRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """결제를 취소하고 구독을 FREE 플랜으로 되돌립니다."""
    result = await db.execute(
        select(Payment).where(
            Payment.imp_uid == body.imp_uid,
            Payment.user_id == current_user.id,
            Payment.status == PaymentStatus.PAID.value,
        )
    )
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="취소할 결제 내역을 찾을 수 없습니다.")

    await cancel_payment(body.imp_uid, body.reason)

    payment.status = PaymentStatus.CANCELLED.value
    payment.cancel_reason = body.reason

    # 구독 플랜 FREE로 변경
    current_user.subscription_plan = "free"
    await db.commit()

    return {"message": "구독이 취소되고 환불이 처리되었습니다."}


@router.get("/history", summary="결제 내역 조회")
async def get_payment_history(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """현재 사용자의 결제 내역을 조회합니다."""
    result = await db.execute(
        select(Payment)
        .where(Payment.user_id == current_user.id)
        .order_by(Payment.created_at.desc())
    )
    payments = result.scalars().all()
    return {
        "total": len(payments),
        "payments": [
            {
                "id": p.id,
                "imp_uid": p.imp_uid,
                "merchant_uid": p.merchant_uid,
                "amount": p.amount,
                "plan": p.plan,
                "status": p.status,
                "created_at": p.created_at.isoformat(),
            }
            for p in payments
        ],
    }
