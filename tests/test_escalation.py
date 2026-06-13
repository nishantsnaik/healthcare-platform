from app.tasks.escalation import _check_escalation_async
from app.models.alert_db import AlertDB
from datetime import datetime
import pytest


@pytest.fixture(scope="module")
def db():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.core.database import Base

    engine = create_engine("sqlite:///./test_escalation.db")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


def test_escalation_none_to_charge_nurse(db):
    # create unacknowledged alert
    alert = AlertDB(
        patient_id=1001,
        alert_type="sepsis alert",
        priority="critical",
        status="new",
        bed="4",
        unit="ICU",
        escalation_level="none",
        created_at=datetime.now()
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    # run escalation
    # assert escalation_level changed
    # assert status is still new


def test_acknowledged_alert_not_escalated(db):
    # create acknowledged alert
    # run escalation
    # assert escalation_level stays at "none"
    pass