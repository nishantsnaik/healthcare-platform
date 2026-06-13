"""
Healthcare Clinical Communication Platform - Main Entry Point

This module is the entry point for the FastAPI application. It sets up:
- The FastAPI app with lifespan management
- Kafka producer for event streaming
- Database initialization
- Route registration
- Logging configuration

FastAPI is a modern, fast web framework for building APIs with Python 3.7+.
It provides automatic validation, documentation, and type hints.
"""

from fastapi import FastAPI

from app.core.kafka_producer import start_producer, stop_producer
from app.routers import alerts
from app.core.logging import configure_logging, get_logger
from datetime import datetime
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from app.core.database import engine, Base

# Load environment variables from .env file
# This keeps sensitive data (API keys, database URLs) out of code
load_dotenv()

# Configure logging for the entire application
# Structured logging helps with debugging and monitoring
configure_logging()

# Get a logger instance for this module
# The __name__ variable automatically becomes "main"
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage the application lifecycle (startup and shutdown events).
    
    This is a lifespan context manager that runs code when the app starts up
    and when it shuts down. It's used for initializing resources that need
    to be properly cleaned up.
    
    The @asynccontextmanager decorator allows us to write async code that
    can be used with 'async with' statements. The 'yield' statement separates
    startup code (before yield) from shutdown code (after yield).
    
    Args:
        app: The FastAPI application instance
        
    Yields:
        Control to the application while it runs
    """
    # STARTUP: Initialize resources
    try:
        # Start the Kafka producer for event streaming
        # Kafka is a distributed event streaming platform
        await start_producer()
    except Exception as e:
        # If Kafka fails to start, we print the error but don't crash
        print(f"Kafka producer failed to start: {e}")
    
    # Create all database tables if they don't exist
    # Base.metadata.create_all looks at all SQLAlchemy models and creates tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("Application started")
    
    # YIELD: The application runs here
    # This is where FastAPI handles incoming requests
    yield
    
    # SHUTDOWN: Clean up resources
    try:
        # Stop the Kafka producer gracefully
        await stop_producer()
    except Exception as e:
        print(f"Kafka producer failed to stop: {e}")
    print("Application shutting down")

# Create the FastAPI application instance
# FastAPI is the web framework that handles HTTP requests and responses
app = FastAPI(
        title="HealthCare Clinical Communication Platform",
        version="1.0.0",
        lifespan=lifespan  # Connect our lifespan manager for startup/shutdown
    )

# Register the alerts router
# This includes all alert-related endpoints (POST, GET, PATCH /alerts)
# Routers help organize API endpoints into logical groups
app.include_router(alerts.router)

@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    
    This is a simple endpoint that returns the application status.
    It's commonly used by monitoring tools to check if the app is running.
    
    Returns:
        dict: A dictionary containing status, version, and timestamp
        
    Example response:
        {
            "status": "ok",
            "version": "1.0",
            "timestamp": "2026-06-12T23:11:00.000000"
        }
    """
    logger.debug("Health check requested")
    return {"status": "ok","version":"1.0","timestamp": datetime.now().isoformat()}

