"""
Assignment Data Models

This module defines Pydantic models for patient-caregiver assignments.
Assignments link patients to caregivers for specific time periods (shifts).

Why time-based assignments?
- Shift-based: Caregivers work in shifts, assignments should reflect this
- Automatic expiration: Assignments automatically end when shift ends
- Historical tracking: We can see who was assigned when

Model inheritance pattern:
- Base: Common fields for all assignment models
- Create: Fields needed when creating a new assignment
- Update: Fields that can be modified
- Response: All fields including database-generated ones

For beginners: These models define which caregiver is responsible for
which patient during a specific time period.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class AssignmentBase(BaseModel):
    """
    Base model containing common assignment fields.
    
    This is the parent class that other assignment models inherit from.
    It contains fields that are shared across all assignment operations.
    
    Attributes:
        patient_id: Unique identifier of the patient
        caregiver_id: Unique identifier of the caregiver
        start_datetime: When the assignment/shift begins
        end_datetime: When the assignment/shift ends (required for time-bound assignments)
    """
    patient_id: int
    caregiver_id: int
    start_datetime: datetime
    end_datetime: datetime


class AssignmentCreate(AssignmentBase):
    """
    Model for creating a new assignment.
    
    This model is used when a client sends a POST request to create an assignment.
    It inherits all fields from AssignmentBase.
    """
    pass


class AssignmentUpdate(BaseModel):
    """
    Model for updating an existing assignment.
    
    This model is used when a client sends a PATCH request to modify an assignment.
    Typically used to extend or end an assignment early.
    
    Attributes:
        end_datetime: New end time for the assignment
    """
    end_datetime: datetime


class Assignment(AssignmentBase):
    """
    Complete assignment model including database-generated fields.
    
    This model represents an assignment as stored in the database, including
    fields that are automatically generated like the ID and timestamps.
    
    Additional attributes beyond AssignmentBase:
        id: Database-generated unique identifier
        created_at: When the assignment record was created
        updated_at: When the assignment record was last modified
    """
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None