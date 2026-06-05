from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class AssignmentBase(BaseModel):
    patient_id: int
    caregiver_id: int
    start_datetime: datetime
    end_datetime: datetime


class AssignmentCreate(AssignmentBase):
    pass

class AssignmentUpdate(BaseModel):
    end_datetime: datetime

class Assignment(AssignmentBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None