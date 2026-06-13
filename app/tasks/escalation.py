"""
Alert Escalation Task Module

This module implements Celery background tasks for alert escalation.
Escalation ensures that unacknowledged alerts are progressively sent to
higher-level caregivers if not responded to within configured time limits.

Escalation levels:
1. none → charge_nurse (after nurse delay)
2. charge_nurse → physician (after charge nurse delay)
3. physician → failsafe (after physician delay)

Why use Celery for escalation?
- Scheduled execution: Tasks run at specific times in the future
- Reliability: Tasks persist even if the server restarts
- Scalability: Can run multiple worker processes
- Retry logic: Automatic retry on failure

For beginners: This shows how to implement background tasks that run
at scheduled times using Celery, a distributed task queue.
"""

from app.core.celery_app import celery_app
from app.core.logging import get_logger
from app.core.database import SyncSessionLocal
from app.models.alert_db import AlertDB

logger = get_logger(__name__)


@celery_app.task
def check_escalation(alert_id: int):
    """
    Check and escalate an alert if it hasn't been acknowledged.
    
    This Celery task is scheduled to run at multiple time intervals after
    an alert is created. Each time it runs, it checks if the alert has been
    acknowledged. If not, it escalates to the next level.
    
    Escalation workflow:
    - If alert is acknowledged: Do nothing (task succeeds silently)
    - If alert is not acknowledged: Move to next escalation level
    - If already at failsafe: Do nothing (already at highest level)
    
    Args:
        alert_id: The unique identifier of the alert to check
        
    Note:
        This uses a synchronous database session because Celery tasks
        don't support async operations. The sync engine is configured in
        database.py.
        
    Example:
        # This is scheduled by the router when creating an alert
        check_escalation.apply_async(args=[alert.id], countdown=300)  # 5 minutes
        check_escalation.apply_async(args=[alert.id], countdown=600)  # 10 minutes
        check_escalation.apply_async(args=[alert.id], countdown=900)  # 15 minutes
    """
    logger.info("Checking alert escalation", alert_id=alert_id)
    
    # Use synchronous database session (Celery doesn't support async)
    with SyncSessionLocal() as db:
        # Fetch the alert from database
        alert = db.get(AlertDB, alert_id)

        # Check if alert still exists
        if alert is None:
            logger.warning("Alert not found for escalation check", alert_id=alert_id)
            return
        
        # Skip escalation if alert has been acknowledged
        if alert.status == "acknowledged":
            logger.info("Alert already acknowledged, skipping escalation", alert_id=alert_id)
            return

        # Get current escalation level
        current_level = alert.escalation_level
        logger.debug("Current escalation level", alert_id=alert_id, level=current_level)

        # Escalate to next level based on current level
        if current_level == "none":
            # First escalation: from none to charge nurse
            logger.info("Escalating alert to charge nurse", alert_id=alert_id)
            alert.escalation_level = "charge_nurse"
        elif current_level == "charge_nurse":
            # Second escalation: from charge nurse to physician
            logger.info("Escalating alert to physician", alert_id=alert_id)
            alert.escalation_level = "physician"
        elif current_level == "physician":
            # Third escalation: from physician to failsafe (highest level)
            logger.warning("Escalating alert to failsafe", alert_id=alert_id)
            alert.escalation_level = "failsafe"
        else:
            # Already at final level or unknown level
            logger.info("Alert already at final escalation level", alert_id=alert_id, level=current_level)

        # Save the escalation level change
        db.commit()
        logger.info("Escalation check complete", alert_id=alert_id, new_level=alert.escalation_level)