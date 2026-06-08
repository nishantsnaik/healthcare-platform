from sqlalchemy import Column, Integer, String, DateTime
from app.core.database import Base

class AlertDB(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, nullable=False)
    alert_type = Column(String, nullable=False)
    priority = Column(String, nullable=False)
    status = Column(String, default="new")
    bed = Column(String, nullable=False)
    unit = Column(String, nullable=False)
    llm_summary = Column(String, nullable=True)
    llm_priority_suggestion = Column(String, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)
    escalation_level = Column(String, default="none")