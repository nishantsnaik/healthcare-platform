"""
Alert Data Models

This module defines Pydantic models for clinical alerts.
Pydantic models provide automatic data validation and serialization.

Why use Pydantic models?
- Automatic validation: Ensures data is correct type and format
- Serialization: Converts Python objects to JSON automatically
- Documentation: Auto-generates API documentation in FastAPI
- Type hints: IDE auto-completion and error checking

Model inheritance pattern:
- Base: Common fields for all alert models
- Create: Fields needed when creating a new alert
- Update: Fields that can be modified (all optional)
- Response: All fields including database-generated ones

For beginners: These are like data contracts that define what an alert looks like
and ensure all data follows the same structure.
"""

from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from typing import Optional


class AlertType(str, Enum):
    """
    Enumeration of possible alert types in the healthcare system.
    
    An Enum (enumeration) is a set of named values. Using enums ensures
    only valid alert types can be used, preventing typos and invalid data.
    
    Values:
        SEPSISALERT: Systemic infection risk - requires immediate attention
        CRITICALLAB: Abnormal laboratory results needing review
        FALLRISK: Patient at risk of falling
        MEDICATIONOVERDUE: Scheduled medication not administered on time
        ABNORMALVITALS: Vital signs outside normal range
    """
    SEPSISALERT = "sepsis alert"
    CRITICALLAB = "critical lab"
    FALLRISK = "fall risk"
    MEDICATIONOVERDUE = "medication overdue"
    ABNORMALVITALS = "Abnormal vitals"


class AlertPriority(str, Enum):
    """
    Enumeration of alert priority levels.
    
    Priority determines how quickly an alert needs attention.
    Higher priority alerts are escalated faster if not acknowledged.
    
    Values:
        CRITICAL: Immediate intervention required - risk to life
        HIGH: Prompt review needed - significant risk if delayed
        MEDIUM: Clinical attention required but not urgent
        LOW: Informational - routine follow-up
    """
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AlertStatus(str, Enum):
    """
    Enumeration of alert status values in the lifecycle.
    
    Status tracks where an alert is in its workflow:
    - NEW: Just created, not yet acknowledged
    - ESCALATED: Sent to higher-level caregiver after timeout
    - ACKNOWLEDGED: Caregiver has seen and is addressing the alert
    
    Values:
        NEW: Alert was just created
        ESCALATED: Alert was escalated to another caregiver
        ACKNOWLEDGED: Alert was acknowledged by a caregiver
    """
    NEW = "new"
    ESCALATED = "escalated"
    ACKNOWLEDGED = "acknowledged"


class AlertBase(BaseModel):
    """
    Base model containing common alert fields.
    
    This is the parent class that other alert models inherit from.
    It contains fields that are shared across all alert operations.
    
    Attributes:
        patient_id: Unique identifier of the patient
        alert_type: Type of clinical alert (from AlertType enum)
        priority: Urgency level (from AlertPriority enum)
        status: Current status in workflow (defaults to NEW)
        bed: Patient bed location (e.g., "ICU-4")
        unit: Hospital unit or department (e.g., "ICU", "ED")
    """
    patient_id: int
    alert_type: AlertType
    priority: AlertPriority
    status : AlertStatus = AlertStatus.NEW  # Default to NEW when creating
    bed: str
    unit: str


class AlertCreate(AlertBase):
    """
    Model for creating a new alert.
    
    This model is used when a client sends a POST request to create an alert.
    It inherits all fields from AlertBase and doesn't add any new ones.
    
    The 'pass' statement means this class is identical to AlertBase.
    We create it separately for clarity and to follow the pattern.
    """
    pass


class AlertUpdate(BaseModel):
    """
    Model for updating an existing alert.
    
    This model is used when a client sends a PATCH request to modify an alert.
    All fields are optional (Optional[...]) because we might only want to
    update one field at a time.
    
    Attributes:
        status: New status if being updated
        acknowledged_at: Timestamp when alert was acknowledged
    """
    status: Optional[AlertStatus] = None
    acknowledged_at: Optional[datetime] = None


class Alert(AlertBase):
    """
    Complete alert model including database-generated fields.
    
    This model represents an alert as stored in the database, including
    fields that are automatically generated like the ID and timestamps.
    It's used when returning data to clients.
    
    Additional attributes beyond AlertBase:
        id: Database-generated unique identifier
        llm_summary: AI-generated summary of the alert (populated asynchronously)
        llm_priority_suggestion: AI-recommended priority level
        acknowledged_at: When the alert was acknowledged
        created_at: When the alert was created
        updated_at: When the alert was last modified
    """
    id: int
    llm_summary: Optional[str] = None  # Populated by background LLM task
    llm_priority_suggestion: Optional[AlertPriority] = None  # AI recommendation
    acknowledged_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
