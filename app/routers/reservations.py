from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app import schemas
from datetime import datetime, timedelta
from app.models import Reservation, Event, ReservationState
from app.auth import get_current_user
from sqlalchemy import select, update

router = APIRouter()


@router.post("/hold", response_model=schemas.ReservationOut)
def create_hold(reservation_in: schemas.ReservationCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    # Transactional - lock event row
    event = db.query(Event).filter(Event.id == reservation_in.event_id).with_for_update().first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if not event.is_active:
        raise HTTPException(status_code=400, detail="Event is not active")
    if event.available_capacity <= 0:
        raise HTTPException(status_code=400, detail="No capacity")
    # Decrement capacity and create hold
    event.available_capacity -= 1
    expires_at = datetime.utcnow() + timedelta(minutes=5)
    reservation = Reservation(user_id=current_user.id, event_id=event.id, state=ReservationState.HOLD, expires_at=expires_at)
    db.add(reservation)
    db.commit()
    db.refresh(reservation)
    return reservation


@router.post("/confirm/{reservation_id}", response_model=schemas.ReservationOut)
def confirm_reservation(reservation_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id, Reservation.user_id == current_user.id).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    if reservation.state != ReservationState.HOLD:
        raise HTTPException(status_code=400, detail="Reservation not in HOLD state")
    # Update to CONFIRMED
    reservation.state = ReservationState.CONFIRMED
    db.commit()
    db.refresh(reservation)
    return reservation
