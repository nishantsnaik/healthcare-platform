from fastapi import FastAPI

from app.core.kafka_producer import start_producer, stop_producer
from app.routers import alerts
from datetime import datetime
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from app.core.database import engine, Base

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # runs on startup
    await start_producer()
    async with engine.begin() as conn:  # ← add ()
        await conn.run_sync(Base.metadata.create_all)  # ← metadata

    print("Application started")
    yield
    # runs on shutdown
    await stop_producer()
    print("Application shutting down")

app = FastAPI(
        title="HealthCare Clinical Communication Platform",
        version="1.0.0",
        lifespan=lifespan
    )

app.include_router(alerts.router)

@app.get("/health")
async def health_check():
    return {"status": "ok","version":"1.0","timestamp": datetime.now().isoformat()}

