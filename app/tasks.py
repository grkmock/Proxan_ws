from datetime import datetime
import app.db as db_module
from app.models import Reservation, ReservationState, Event
from datetime import datetime


def cleanup_expired_holds():
    SessionLocal = db_module.SessionLocal
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        expired = db.query(Reservation).filter(Reservation.state == ReservationState.HOLD, Reservation.expires_at <= now).all()
        for r in expired:
            # restore capacity
            event = db.query(Event).filter(Event.id == r.event_id).with_for_update().first()
            if event:
                event.available_capacity += 1
            db.delete(r)
        db.commit()
    finally:
        db.close()
