"""
Alerts Router Module

This module defines the API endpoints (routes) for alert operations.
Routers organize related endpoints together and make the codebase modular.

FastAPI routers provide:
- Automatic URL routing
- Request validation using Pydantic models
- Response serialization
- Automatic API documentation (Swagger UI)

Endpoints defined:
- POST /alerts/ - Create a new alert
- GET /alerts/{alert_id} - Retrieve a specific alert
- PATCH /alerts/{alert_id} - Update an alert (typically to acknowledge)

For beginners: This file defines the API interface - how external systems
interact with the alert management system.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.kafka_producer import publish_alert_created
from app.core.logging import get_logger
from app.models.alert import Alert, AlertCreate, AlertUpdate, AlertPriority, AlertStatus
from datetime import datetime
from app.repositories.alerts import save_alert, fetch_alert
from app.services.llm_service import generate_llm_summary
from app.tasks.escalation import check_escalation
from app.core.config import settings

# Get a logger instance for this module
logger = get_logger(__name__)

# Create the router instance
# prefix="/alerts" means all routes start with /alerts
# tags=["alerts"] groups these endpoints in the API documentation
router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.post("/", response_model=Alert)
async def create_alert(alert_data: AlertCreate,
                       background_tasks: BackgroundTasks,
                       db: AsyncSession = Depends(get_db)):
    """
    Create a new clinical alert.
    
    This endpoint creates a new alert and schedules several background tasks:
    1. Saves the alert to the database
    2. Schedules escalation checks at multiple time intervals
    3. Publishes an event to Kafka for other services
    4. Triggers LLM summarization in the background
    
    The response returns immediately with the created alert, while background
    tasks run asynchronously. This keeps the API fast even though LLM processing
    can take several seconds.
    
    Args:
        alert_data: Alert data validated by AlertCreate model
        background_tasks: FastAPI BackgroundTasks for async operations
        db: Database session injected by FastAPI dependency injection
        
    Returns:
        Alert: The created alert with database-generated fields
        
    Example request:
        POST /alerts/
        {
            "patient_id": 1001,
            "alert_type": "sepsis alert",
            "priority": "critical",
            "bed": "4",
            "unit": "ICU"
        }
    """
    logger.info("Creating new alert", patient_id=alert_data.patient_id, alert_type=alert_data.alert_type, priority=alert_data.priority)
    
    # Save alert to database
    # model_dump(mode="json") converts Pydantic model to dictionary
    alert = await save_alert(db, alert_data.model_dump(mode="json"))

    # Schedule escalation checks using Celery
    # Celery is a task queue that runs tasks in the background
    # We schedule multiple checks at different delays for escalation levels
    logger.info("Scheduling escalation tasks", alert_id=alert.id, nurse_delay=settings.escalation_nurse_delay, charge_nurse_delay=settings.escalation_charge_nurse_delay, physician_delay=settings.escalation_physician_delay)
    check_escalation.apply_async(args=[alert.id], countdown=settings.escalation_nurse_delay)
    check_escalation.apply_async(args=[alert.id], countdown=settings.escalation_charge_nurse_delay)
    check_escalation.apply_async(args=[alert.id], countdown=settings.escalation_physician_delay)

    # Publish event to Kafka for event streaming
    # Other services can subscribe to this topic for real-time updates
    await publish_alert_created(alert.id, alert.patient_id, alert.created_at.isoformat())
    
    # Add LLM summarization task to background
    # This doesn't block the response - runs in the background
    background_tasks.add_task(generate_llm_summary, alert.id)
    
    logger.info("Alert created successfully", alert_id=alert.id)
    return alert


@router.get("/{alert_id}")
async def get_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retrieve a specific alert by ID.
    
    This endpoint fetches an alert from the database. If the LLM background
    task has completed, the response will include the AI-generated summary.
    
    Args:
        alert_id: The unique identifier of the alert
        db: Database session injected by FastAPI dependency injection
        
    Returns:
        Alert: The alert with all fields including LLM summary if available
        
    Raises:
        HTTPException: 404 error if alert not found
        
    Example request:
        GET /alerts/1
    """
    logger.debug("Fetching alert", alert_id=alert_id)
    alert = await fetch_alert(db, alert_id)
    
    if not alert:
        logger.warning("Alert not found", alert_id=alert_id)
        raise HTTPException(status_code=404, detail="Alert not found")
    
    logger.debug("Alert fetched successfully", alert_id=alert_id)
    return alert


@router.patch("/{alert_id}", response_model=Alert)
async def update_alerts(
    alert_id: int,
    alert_update: AlertUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update an alert (typically to acknowledge it).
    
    This endpoint is primarily used to acknowledge alerts when a caregiver
    responds. It can also update other fields if needed.
    
    When status is set to ACKNOWLEDGED:
    - The acknowledged_at timestamp is automatically set
    - Escalation tasks will skip this alert (already handled)
    
    Args:
        alert_id: The unique identifier of the alert
        alert_update: Fields to update (validated by AlertUpdate model)
        db: Database session injected by FastAPI dependency injection
        
    Returns:
        Alert: The updated alert with all fields
        
    Raises:
        HTTPException: 404 error if alert not found
        
    Example request:
        PATCH /alerts/1
        {
            "status": "acknowledged"
        }
    """
    logger.info("Updating alert", alert_id=alert_id, status_update=alert_update.status)
    alert = await fetch_alert(db, alert_id)
    
    if not alert:
        logger.warning("Alert not found for update", alert_id=alert_id)
        raise HTTPException(status_code=404, detail="Alert not found")
    
    # Update status if provided
    if alert_update.status is not None:
        alert.status = alert_update.status
    
    # Set acknowledgment timestamp if status is acknowledged
    if alert.status == AlertStatus.ACKNOWLEDGED:
        alert.acknowledged_at = datetime.now()
        logger.info("Alert acknowledged", alert_id=alert_id, acknowledged_at=alert.acknowledged_at)
    
    # Persist changes to database
    await db.commit()          # Save the changes
    await db.refresh(alert)    # Refresh to get any database-generated values
    
    logger.info("Alert updated successfully", alert_id=alert_id, new_status=alert.status)
    return alert

