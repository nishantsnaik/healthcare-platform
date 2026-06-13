"""
Alert Repository Module

This module implements the Repository pattern for alert data access.
The Repository pattern abstracts database operations, providing a clean
interface between the business logic and the data layer.

Why use the Repository pattern?
- Separation of concerns: Business logic doesn't need to know about database details
- Testability: Can mock repositories for unit testing
- Maintainability: Database queries are centralized in one place
- Reusability: Same repository can be used by multiple services

For beginners: Think of repositories as a collection of functions that
handle all database operations for a specific entity (alerts in this case).
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert_db import AlertDB
from app.core.logging import get_logger
from datetime import datetime

logger = get_logger(__name__)


async def fetch_alert(db: AsyncSession, alert_id: int) -> AlertDB | None:
    """
    Fetch an alert from the database by ID.
    
    This function retrieves a single alert from the database using its
    primary key. It returns None if the alert doesn't exist.
    
    Args:
        db: The async database session
        alert_id: The unique identifier of the alert to fetch
        
    Returns:
        AlertDB: The alert object if found, None otherwise
        
    Example:
        alert = await fetch_alert(db, 123)
        if alert:
            print(f"Alert: {alert.alert_type}")
    """
    logger.debug("Fetching alert from database", alert_id=alert_id)
    # db.get() is a SQLAlchemy method to fetch by primary key
    alert = await db.get(AlertDB, alert_id)
    
    if alert:
        logger.debug("Alert fetched successfully", alert_id=alert_id)
    else:
        logger.debug("Alert not found in database", alert_id=alert_id)
    
    return alert


async def save_alert(db: AsyncSession, alert_data: dict) -> AlertDB:
    """
    Save a new alert to the database.
    
    This function creates a new alert record in the database. It automatically
    sets the created_at timestamp and returns the alert with its database-generated ID.
    
    Args:
        db: The async database session
        alert_data: Dictionary containing alert fields (patient_id, alert_type, etc.)
        
    Returns:
        AlertDB: The saved alert object with the auto-generated ID
        
    Example:
        alert_data = {
            "patient_id": 1001,
            "alert_type": "sepsis alert",
            "priority": "critical",
            "bed": "4",
            "unit": "ICU"
        }
        alert = await save_alert(db, alert_data)
        print(f"Created alert with ID: {alert.id}")
    """
    logger.info("Saving alert to database", patient_id=alert_data.get("patient_id"), alert_type=alert_data.get("alert_type"))
    
    # Create AlertDB instance from dictionary
    # **alert_data unpacks the dictionary into keyword arguments
    alert = AlertDB(
        **alert_data,
        created_at=datetime.now()  # Set creation timestamp
    )
    
    # Add to session and commit to database
    db.add(alert)
    await db.commit()
    
    # Refresh to get the auto-generated ID and any database defaults
    await db.refresh(alert)
    
    logger.info("Alert saved successfully", alert_id=alert.id)
    return alert
