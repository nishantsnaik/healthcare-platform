"""
Patient Data Models

This module defines Pydantic models for patient information.
Patients are the core entity in the healthcare system - alerts are
created for patients, and caregivers are assigned to patients.

Model inheritance pattern:
- Base: Common fields for all patient models
- Create: Fields needed when creating a new patient
- Update: Fields that can be modified (all optional)
- Response: All fields including database-generated ones

For beginners: These models define what patient data looks like and ensure
all patient records follow the same structure.
"""

from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime, date
from typing import Optional


class PatientStatus(str, Enum):
    """
    Enumeration of possible patient statuses.
    
    Status tracks the patient's current state in the healthcare system.
    This helps determine which patients are currently admitted and need care.
    
    Values:
        INACTIVE: Patient record exists but not currently in system
        ADMITTED: Patient is currently admitted and receiving care
        DISCHARGED: Patient has been discharged from the facility
        DECEASED: Patient has passed away
    """
    INACTIVE = "inactive"
    ADMITTED = "admitted"
    DISCHARGED = "discharged"
    DECEASED = "deceased"


class PatientBase(BaseModel):
    """
    Base model containing common patient fields.
    
    This is the parent class that other patient models inherit from.
    It contains fields that are shared across all patient operations.
    
    Attributes:
        name: Patient's full name
        dob: Date of birth
        mrn: Medical Record Number (facility-prefixed, e.g., "MGH-100123")
        facility: Healthcare facility name (optional)
        unit: Hospital unit or department (optional)
        status: Current patient status (optional)
    """
    name: str
    dob: date
    mrn: str
    facility: Optional[str]
    unit: Optional[str]
    status: Optional[PatientStatus]


class PatientCreate(PatientBase):
    """
    Model for creating a new patient.
    
    This model is used when a client sends a POST request to create a patient.
    It inherits all fields from PatientBase.
    """
    pass


class PatientUpdate(BaseModel):
    """
    Model for updating an existing patient.
    
    This model is used when a client sends a PATCH request to modify a patient.
    All fields are optional because we might only want to update one field.
    
    Attributes:
        facility: New facility if being updated
        unit: New unit if being updated
        status: New status if being updated
    """
    facility: Optional[str] = None
    unit: Optional[str] = None
    status: Optional[PatientStatus] = None


class Patient(PatientCreate):
    """
    Complete patient model including database-generated fields.
    
    This model represents a patient as stored in the database, including
    fields that are automatically generated like the ID and timestamps.
    
    Additional attributes beyond PatientBase:
        id: Database-generated unique identifier
        created_at: When the patient record was created
        updated_at: When the patient record was last modified
    """
    id: int
    created_at: datetime
    updated_at: Optional[datetime]










