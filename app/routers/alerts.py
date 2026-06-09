from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.kafka_producer import publish_alert_created
from app.models.alert import Alert, AlertCreate, AlertUpdate, AlertPriority, AlertStatus
from datetime import datetime
from app.repositories.alerts import save_alert, fetch_alert
from app.services.llm_service import generate_llm_summary
from app.tasks.escalation import check_escalation
from app.core.config import settings

router = APIRouter(prefix="/alerts", tags=["alerts"])

@router.post("/", response_model=Alert)
async def create_alert(alert_data: AlertCreate,
                       background_tasks: BackgroundTasks,
                       db: AsyncSession = Depends(get_db)):
    alert = await save_alert(db, alert_data.model_dump(mode="json"))

    check_escalation.apply_async(args=[alert.id], countdown=settings.escalation_nurse_delay)
    check_escalation.apply_async(args=[alert.id], countdown=settings.escalation_charge_nurse_delay)
    check_escalation.apply_async(args=[alert.id], countdown=settings.escalation_physician_delay)

    await publish_alert_created(alert.id, alert.patient_id, alert.created_at.isoformat())
    background_tasks.add_task(generate_llm_summary, alert.id)
    return alert

@router.get("/{alert_id}")
async def get_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    alert = await fetch_alert(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert

@router.patch("/{alert_id}", response_model=Alert)
async def update_alerts(
    alert_id: int,
    alert_update: AlertUpdate,
    db: AsyncSession = Depends(get_db)
):
    alert = await fetch_alert(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    if alert_update.status is not None:
        alert.status = alert_update.status
    if alert.status == AlertStatus.ACKNOWLEDGED:
        alert.acknowledged_at = datetime.now()
    await db.commit()          # ← persist the update
    await db.refresh(alert)    # ← get fresh data
    return alert

