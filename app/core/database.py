from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite+aiosqlite:///./healthcare.db"

engine = create_async_engine(DATABASE_URL, echo=True)  # echo=True logs all SQL
Base = declarative_base()
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False    # ← add this
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session