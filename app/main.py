# StudyMate FastAPI 앱 엔트리포인트
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import create_tables
from app.routers import quiz, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작 시 DB 테이블 자동 생성"""
    await create_tables()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI 문제 생성 + 오답 분석 학습 도우미. Gemini API로 과목별 퀴즈를 생성하고 취약점을 분석합니다.",
    lifespan=lifespan,
)

# CORS 설정 (개발 환경)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(users.router)
app.include_router(quiz.router)


@app.get("/", tags=["health"])
async def root():
    """헬스 체크 엔드포인트"""
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["health"])
async def health():
    """서버 상태 확인"""
    return {"status": "ok"}
