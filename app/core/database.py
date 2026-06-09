from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy import create_engine
from app.core.config import settings

# async — for FastAPI
engine = create_async_engine(settings.database_url, echo=True)
Base = declarative_base()
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# sync — for Celery
SYNC_DATABASE_URL = settings.database_url.replace(
    "postgresql+asyncpg", "postgresql+psycopg2"
)
sync_engine = create_engine(SYNC_DATABASE_URL)
SyncSessionLocal = sessionmaker(sync_engine)

async def get_db():
    async with AsyncSessionLocal() as session:   # ← async session for FastAPI
        yield session