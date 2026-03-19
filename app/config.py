# 환경변수 설정 모듈
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Gemini API 키
    gemini_api_key: str = ""

    # 데이터베이스 URL (SQLite 기본값)
    database_url: str = "sqlite+aiosqlite:///./studymate.db"

    # JWT 시크릿 키
    secret_key: str = "change-this-in-production"

    # JWT 알고리즘 및 만료 시간 (분)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24시간

    # 디버그 모드
    debug: bool = True

    # 앱 메타정보
    app_name: str = "StudyMate"
    app_version: str = "0.1.0"

    # 포트원(PortOne) 결제 연동
    portone_api_key: str = ""
    portone_api_secret: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """설정 싱글톤 반환 (캐시 사용)"""
    return Settings()


settings = get_settings()
