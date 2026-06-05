from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from typing import Optional


"""
Caregiver
- id, name, jid
- role: RoleEnum
- unit: str
- availability: AvailabilityEnum
"""

class Role(str, Enum):
    NURSE = "nurse"
    PHYSICIAN = "physician"
    CARECOORDINATOR = "care_coordinator"
    RESPIRATORYTHERAPIST = "respiratory_therapist"

class Availability(str, Enum):
    ONBOARDING = "onboarding"
    AVAILABLE = "available"
    BUSY = "busy"
    OFFDUTY = "off_duty"

class CaregiverBase(BaseModel):
    name: str
    role: Role
    jid: str
    unit: Optional[str]
    availability: Availability = Availability.ONBOARDING

class CaregiverCreate(CaregiverBase):
    pass

class Caregiver(CaregiverCreate):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None