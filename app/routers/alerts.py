from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.models.alert import Alert, AlertCreate, AlertUpdate, AlertPriority, AlertStatus
from datetime import datetime
from app.repositories.alerts import alerts_db, get_next_int, save_alert, fetch_alert
from app.services.llm_service import generate_llm_summary




router = APIRouter(prefix="/alerts", tags=["alerts"])

@router.post("/", response_model=Alert)
async def create_alert(alert_data: AlertCreate,
                       background_tasks: BackgroundTasks):

    alert = Alert(id = get_next_int(),
                  **alert_data.model_dump(),
                  #patient_id=alert_data.patient_id,
                  #alert_type=alert_data.alert_type,
                  #priority=alert_data.priority,
                  #bed=alert_data.bed,
                  #unit=alert_data.unit,
                  #status=alert_data.status,
                  llm_summary = None,
                  llm_priority_suggestion = None,
                  created_at = datetime.now())
    save_alert(alert)
    background_tasks.add_task(generate_llm_summary, alert.id)
    return alert

@router.get("/{alert_id}")
async def get_alert(alert_id: int):
    alert = fetch_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert

@router.patch("/{alert_id}", response_model=Alert)
async def update_alerts(alert_id: int, alert_update: AlertUpdate):
    alert = alerts_db.get(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    if alert_update.status is not None:
        alert.status = alert_update.status
    if alert.status == AlertStatus.ACKNOWLEDGED:
        alert.acknowledged_at = datetime.now()
    return alert

