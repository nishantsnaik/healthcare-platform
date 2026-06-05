from fastapi import FastAPI
from app.routers import alerts
from datetime import datetime
from contextlib import asynccontextmanager
from dotenv import load_dotenv


load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # runs on startup
    print("Application started")
    yield
    # runs on shutdown
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

