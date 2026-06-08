from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert_db import AlertDB
from datetime import datetime

async def fetch_alert(db: AsyncSession, alert_id: int) -> AlertDB | None:
    return await db.get(AlertDB, alert_id) # ← async, returns actual alert

async def save_alert(db: AsyncSession, alert_data: dict) -> AlertDB:
    alert = AlertDB(
        **alert_data,
        created_at=datetime.now()
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)   # ← gets the auto-generated id back
    return alert
