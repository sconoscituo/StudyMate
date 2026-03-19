# SQLAlchemy 비동기 데이터베이스 설정
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


# 비동기 엔진 생성
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,  # 디버그 모드에서 SQL 쿼리 출력
    future=True,
)

# 비동기 세션 팩토리
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    """모든 모델의 베이스 클래스"""
    pass


async def get_db() -> AsyncSession:
    """FastAPI 의존성 주입용 DB 세션 생성기"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables():
    """애플리케이션 시작 시 테이블 자동 생성"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
