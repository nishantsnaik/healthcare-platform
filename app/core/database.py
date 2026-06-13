"""
Database Configuration Module

This module sets up database connections for the application.
It provides both async and sync database sessions for different use cases.

Why two database engines?
- Async engine: Used by FastAPI for non-blocking database operations
- Sync engine: Used by Celery tasks which don't support async operations

SQLAlchemy is a popular Python SQL toolkit and ORM (Object-Relational Mapper).
It allows us to work with databases using Python classes instead of raw SQL.

For beginners: Think of this as the bridge between your Python code
and the PostgreSQL database.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy import create_engine
from app.core.config import settings

# Async database engine for FastAPI
# Async operations don't block the event loop, allowing the server to handle
# multiple requests concurrently
engine = create_async_engine(settings.database_url, echo=True)

# Base class for all database models
# All SQLAlchemy models will inherit from this Base class
Base = declarative_base()

# Async session factory
# This creates database sessions for FastAPI endpoints
# expire_on_commit=False prevents objects from being expired after commit
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Sync database engine for Celery
# Celery tasks run in separate worker processes and don't support async
# We need to replace the async driver (asyncpg) with a sync one (psycopg2)
SYNC_DATABASE_URL = settings.database_url.replace(
    "postgresql+asyncpg", "postgresql+psycopg2"
)
sync_engine = create_engine(SYNC_DATABASE_URL)

# Sync session factory for Celery tasks
SyncSessionLocal = sessionmaker(sync_engine)

async def get_db():
    """
    Dependency function that provides database sessions to FastAPI endpoints.
    
    This is a FastAPI dependency that yields a database session for each request.
    The 'async with' statement ensures the session is properly closed after use.
    
    How it works:
    1. FastAPI calls this function before each request that needs a database
    2. A new database session is created
    3. The session is yielded to the endpoint function
    4. After the endpoint completes, the session is automatically closed
    
    Yields:
        AsyncSession: A database session for async operations
        
    Example usage in an endpoint:
        @app.get("/alerts/{alert_id}")
        async def get_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
            alert = await db.get(AlertDB, alert_id)
            return alert
    """
    async with AsyncSessionLocal() as session:   # Create and use async session
        yield session