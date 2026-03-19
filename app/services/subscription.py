"""StudyMate 구독 플랜"""
from enum import Enum

class PlanType(str, Enum):
    FREE = "free"
    STUDENT = "student"  # 월 4,900원 (학생 할인)
    PRO = "pro"          # 월 9,900원

PLAN_LIMITS = {
    PlanType.FREE:    {"daily_questions": 10, "ai_explanation": False, "mock_exam": False, "progress_analytics": False},
    PlanType.STUDENT: {"daily_questions": 100,"ai_explanation": True,  "mock_exam": True,  "progress_analytics": False},
    PlanType.PRO:     {"daily_questions": 999,"ai_explanation": True,  "mock_exam": True,  "progress_analytics": True},
}

PLAN_PRICES_KRW = {PlanType.FREE: 0, PlanType.STUDENT: 4900, PlanType.PRO: 9900}
