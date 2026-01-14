import asyncio
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timedelta

from app.main import app
from app.db import Base
import app.db as db_module
from app.tasks import cleanup_expired_holds
from app.models import ReservationState, Reservation


@pytest.fixture(scope="module")
def test_engine():
    # In-memory SQLite must use StaticPool to persist across connections/threads during testing
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="module")
def session_local(test_engine):
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    # Patch the app's DB session factory to use test DB
    db_module.engine = test_engine
    db_module.SessionLocal = SessionLocal
    yield SessionLocal


@pytest.mark.asyncio
async def test_full_reservation_flow(session_local):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Register user
        r = await ac.post("/auth/register", json={"username": "alice", "password": "secret"})
        assert r.status_code == 200
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create event with capacity 5
        r = await ac.post("/events/", json={"title": "Concert", "capacity": 5}, headers=headers)
        assert r.status_code == 200
        event = r.json()
        event_id = event["id"]
        assert event["available_capacity"] == 5

        # Create 5 holds sequentially (SQLite in-memory does not support concurrent row locking)
        results = []
        for _ in range(5):
            resp = await ac.post("/reservations/hold", json={"event_id": event_id}, headers=headers)
            assert resp.status_code == 200
            results.append(resp)
        reservations = [r.json() for r in results]
        assert len(reservations) == 5

        # One more should fail (no capacity)
        r = await ac.post("/reservations/hold", json={"event_id": event_id}, headers=headers)
        assert r.status_code == 400

        # Confirm the first reservation
        res_id = reservations[0]["id"]
        r = await ac.post(f"/reservations/confirm/{res_id}", headers=headers)
        assert r.status_code == 200
        confirmed = r.json()
        assert confirmed["state"] == "CONFIRMED"

        # Check event available_capacity is 0
        r = await ac.get(f"/events/{event_id}")
        assert r.status_code == 200
        evt = r.json()
        assert evt["available_capacity"] == 0

        # Expire remaining holds by updating DB directly
        SessionLocal = session_local
        db = SessionLocal()
        try:
            now = datetime.utcnow()
            holds = db.query(Reservation).filter(Reservation.event_id == event_id, Reservation.state == ReservationState.HOLD).all()
            assert len(holds) == 4
            for h in holds:
                h.expires_at = now - timedelta(minutes=1)
            db.commit()
        finally:
            db.close()

        # Run cleanup task which should remove expired holds and restore capacity
        cleanup_expired_holds()

        # Check event available capacity is now 4
        r = await ac.get(f"/events/{event_id}")
        evt = r.json()
        assert evt["available_capacity"] == 4

        # Also ensure holds are removed
        SessionLocal = session_local
        db = SessionLocal()
        try:
            remaining_holds = db.query(Reservation).filter(Reservation.event_id == event_id, Reservation.state == ReservationState.HOLD).count()
            assert remaining_holds == 0
        finally:
            db.close()
