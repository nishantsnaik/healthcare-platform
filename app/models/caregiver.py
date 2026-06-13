"""
Caregiver Data Models

This module defines Pydantic models for caregiver (healthcare staff) information.
Caregivers are the healthcare professionals who receive and respond to alerts.

Model inheritance pattern:
- Base: Common fields for all caregiver models
- Create: Fields needed when creating a new caregiver
- Response: All fields including database-generated ones

For beginners: These models define what caregiver data looks like and ensure
all caregiver records follow the same structure.
"""

from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from typing import Optional


class Role(str, Enum):
    """
    Enumeration of caregiver roles in the healthcare system.
    
    Different roles have different responsibilities and may receive
    different types of alerts based on their expertise.
    
    Values:
        NURSE: Registered nurse providing direct patient care
        PHYSICIAN: Doctor responsible for medical decisions
        CARECOORDINATOR: Staff coordinating patient care across departments
        RESPIRATORYTHERAPIST: Specialist treating respiratory conditions
    """
    NURSE = "nurse"
    PHYSICIAN = "physician"
    CARECOORDINATOR = "care_coordinator"
    RESPIRATORYTHERAPIST = "respiratory_therapist"


class Availability(str, Enum):
    """
    Enumeration of caregiver availability status.
    
    This tracks whether a caregiver is currently able to receive alerts.
    The system only sends alerts to available caregivers.
    
    Values:
        ONBOARDING: New caregiver being set up in the system
        AVAILABLE: Caregiver is on duty and can receive alerts
        BUSY: Caregiver is occupied with another task
        OFFDUTY: Caregiver is not currently working
    """
    ONBOARDING = "onboarding"
    AVAILABLE = "available"
    BUSY = "busy"
    OFFDUTY = "off_duty"


class CaregiverBase(BaseModel):
    """
    Base model containing common caregiver fields.
    
    This is the parent class that other caregiver models inherit from.
    It contains fields that are shared across all caregiver operations.
    
    Attributes:
        name: Caregiver's full name
        role: Healthcare role (from Role enum)
        jid: Internal system identifier for the caregiver
        unit: Hospital unit or department (optional)
        availability: Current availability status (defaults to ONBOARDING)
    """
    name: str
    role: Role
    jid: str
    unit: Optional[str]
    availability: Availability = Availability.ONBOARDING


class CaregiverCreate(CaregiverBase):
    """
    Model for creating a new caregiver.
    
    This model is used when a client sends a POST request to create a caregiver.
    It inherits all fields from CaregiverBase.
    """
    pass


class Caregiver(CaregiverCreate):
    """
    Complete caregiver model including database-generated fields.
    
    This model represents a caregiver as stored in the database, including
    fields that are automatically generated like the ID and timestamps.
    
    Additional attributes beyond CaregiverBase:
        id: Database-generated unique identifier
        created_at: When the caregiver record was created
        updated_at: When the caregiver record was last modified
    """
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None