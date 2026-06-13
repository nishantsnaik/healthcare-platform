"""
Alert Database Model (SQLAlchemy)

This module defines the SQLAlchemy database model for alerts.
SQLAlchemy is an ORM (Object-Relational Mapper) that allows us to work
with database tables using Python classes instead of raw SQL.

Difference from Pydantic models:
- Pydantic models (alert.py): For API validation and serialization
- SQLAlchemy models (alert_db.py): For database table structure

This model maps to the "alerts" table in the PostgreSQL database.

For beginners: This defines how alert data is stored in the database.
Each attribute becomes a column in the database table.
"""

from sqlalchemy import Column, Integer, String, DateTime
from app.core.database import Base


class AlertDB(Base):
    """
    SQLAlchemy database model for the alerts table.
    
    This class defines the structure of the alerts table in the database.
    It inherits from Base, which is the declarative base defined in database.py.
    
    Table name: "alerts"
    
    Attributes:
        id: Primary key, auto-incremented unique identifier
        patient_id: Foreign key reference to the patient
        alert_type: Type of clinical alert (stored as string)
        priority: Urgency level (stored as string)
        status: Current status in workflow (defaults to "new")
        bed: Patient bed location
        unit: Hospital unit or department
        llm_summary: AI-generated summary (nullable, populated asynchronously)
        llm_priority_suggestion: AI-recommended priority (nullable)
        acknowledged_at: Timestamp when alert was acknowledged (nullable)
        created_at: When the alert was created
        updated_at: When the alert was last modified (nullable)
        escalation_level: Current escalation level (defaults to "none")
    
    Note: This is the database model. For API models, see app/models/alert.py
    """
    __tablename__ = "alerts"

    # Primary key - unique identifier for each alert
    # autoincrement=True means the database automatically assigns IDs
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key reference to patient
    patient_id = Column(Integer, nullable=False)
    
    # Alert metadata (stored as strings, validated by Pydantic models)
    alert_type = Column(String, nullable=False)
    priority = Column(String, nullable=False)
    status = Column(String, default="new")
    
    # Location information
    bed = Column(String, nullable=False)
    unit = Column(String, nullable=False)
    
    # AI-generated fields (nullable because they're populated asynchronously)
    llm_summary = Column(String, nullable=True)
    llm_priority_suggestion = Column(String, nullable=True)
    
    # Timestamps
    acknowledged_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)
    
    # Escalation tracking
    escalation_level = Column(String, default="none")