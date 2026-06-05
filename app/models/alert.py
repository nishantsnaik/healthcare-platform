from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from typing import Optional


class AlertType(str, Enum):
    SEPSISALERT = "sepsis alert"
    CRITICALLAB = "critical lab"
    FALLRISK = "fall risk"
    MEDICATIONOVERDUE = "medication overdue"
    ABNORMALVITALS = "Abnormal vitals"

class AlertPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class AlertStatus(str, Enum):
    NEW = "new"
    ESCALATED = "escalated"
    ACKNOWLEDGED = "acknowledged"

class AlertBase(BaseModel):
    patient_id: int
    alert_type: AlertType
    priority: AlertPriority
    status : AlertStatus = AlertStatus.NEW
    bed: str
    unit: str

class AlertCreate(AlertBase):
    pass

class AlertUpdate(BaseModel):
    status: Optional[AlertStatus] = None
    acknowledged_at: Optional[datetime] = None

class Alert(AlertBase):
    id: int
    llm_summary: Optional[str] = None
    llm_priority_suggestion: Optional[AlertPriority] = None
    acknowledged_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
