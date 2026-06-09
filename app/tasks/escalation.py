from app.core.celery_app import celery_app
import asyncio

from app.repositories.alerts import fetch_alert

from sqlalchemy.orm import Session
from app.core.database import SyncSessionLocal
from app.models.alert_db import AlertDB

from sqlalchemy.orm import Session
from app.core.database import SyncSessionLocal
from app.models.alert_db import AlertDB


@celery_app.task
def check_escalation(alert_id: int):
    with SyncSessionLocal() as db:
        alert = db.get(AlertDB, alert_id)

        if alert is None:
            return
        if alert.status == "acknowledged":
            return

        current_level = alert.escalation_level
        print(f"DEBUG: alert {alert_id} level={current_level}")

        if current_level == "none":
            print(f"Escalating Alert {alert_id} → charge nurse")
            alert.escalation_level = "charge_nurse"
        elif current_level == "charge_nurse":
            print(f"Escalating Alert {alert_id} → physician")
            alert.escalation_level = "physician"
        elif current_level == "physician":
            print(f"Escalating Alert {alert_id} → FAILSAFE")
            alert.escalation_level = "failsafe"

        db.commit()