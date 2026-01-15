from sqlalchemy.orm import Session
from datetime import datetime
from app.db import SessionLocal
from app.models import Reservation, Event, ReservationState

def cleanup_expired_holds(db_session: Session = None):
    # Eğer bir session verilmemişse (normal çalışma), yenisini aç
    db = db_session or SessionLocal()
    try:
        expired_reservations = db.query(Reservation).filter(
            Reservation.state == ReservationState.HOLD,
            Reservation.expires_at < datetime.utcnow()
        ).all()

        for res in expired_reservations:
            event = db.query(Event).filter(Event.id == res.event_id).first()
            if event:
                event.available_capacity += 1
            db.delete(res)
        
        db.commit()
    except Exception as e:
        print(f"Cleanup Error: {e}")
        db.rollback()
    finally:
        # Sadece biz açtıysak biz kapatmalıyız
        if db_session is None:
            db.close()