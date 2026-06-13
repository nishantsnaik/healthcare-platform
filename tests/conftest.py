import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine as sync_create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.database import Base, get_db    # ← Base and get_db
from main import app                           # ← FastAPI app

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(
    TEST_DATABASE_URL
)
TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session


@pytest.fixture(scope="module")
def client():
    from sqlalchemy import create_engine as sync_create_engine
    sync_engine = sync_create_engine("sqlite:///./test.db")
    Base.metadata.create_all(bind=sync_engine)

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app, raise_server_exceptions=True) as c:  # ← use context manager
        yield c

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=sync_engine)