"""
Patient
- id, mrn (facility-prefixed), name, dob
- unit: UnitEnum
- status: PatientStatusEnum
- facility: str

Alert
- id, patient_id
- alert_type: AlertTypeEnum      ← WHAT happened
- alert_priority: PriorityEnum   ← HOW urgent
- alert_status: AlertStatusEnum  ← WHERE in lifecycle
- bed: str, unit: UnitEnum
- created_at, acknowledged_at

Caregiver
- id, name, jid
- role: RoleEnum
- unit: UnitEnum
- availability: AvailabilityEnum

Assignment
- id, patient_id, caregiver_id
- start_datetime, end_datetime   ← you got this

Message                          ← still needs designing
"""

from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime, date
from typing import Optional

class PatientStatus(str, Enum):
    INACTIVE = "inactive"
    ADMITTED = "admitted"
    DISCHARGED = "discharged"
    DECEASED = "deceased"


class PatientBase(BaseModel):
    name: str
    dob: date
    mrn: str
    facility: Optional[str]
    unit: Optional[str]
    status: Optional[PatientStatus]

class PatientCreate(PatientBase):
    pass

class PatientUpdate(BaseModel):
    facility: Optional[str] = None
    unit: Optional[str] = None
    status: Optional[PatientStatus] = None

class Patient(PatientCreate):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]




"""
class AlertTypeEnum:
    SEPSIS = "Sepsis Alert"
    CRITICAL = "Critical Lab"
    FALL = "Fall Risk"

class PriorityEnum:
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class AlertStatusEnum:
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    ESCALATED = "escalated"
"""










