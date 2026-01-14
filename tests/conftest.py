from datetime import datetime, timedelta
import pytest
from app import models
from app.models import ReservationState


@pytest.fixture
def hold_reservation(db):
    reservation = models.Reservation(
        event_id=1,
        user_id=1,
        state=ReservationState.HOLD,
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
        state=ReservationState.HOLD,
        expires_at=datetime.utcnow() - timedelta(minutes=5)
    )
    db.add(reservation)
    db.commit()
    db.refresh(reservation)
    return reservation
