import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db import SessionLocal
from app import models
from datetime import datetime, timedelta

@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def hold_reservation(db):
    reservation = models.Reservation(
        event_id=1,
        user_id=1,
        status="HELD",
        expires_at=datetime.utcnow() + timedelta(minutes=5)
    )
    db.add(reservation)
    db.commit()
    db.refresh(reservation)
    return reservation


@pytest.fixture
def expired_hold(db):
    reservation = models.Reservation(
        event_id=1,
        user_id=1,
        status="HELD",
        expires_at=datetime.utcnow() - timedelta(minutes=5)
    )
    db.add(reservation)
    db.commit()
    db.refresh(reservation)
    return reservation
