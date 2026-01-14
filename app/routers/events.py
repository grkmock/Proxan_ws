from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app import schemas
from app.models import Event, Reservation, ReservationState
from sqlalchemy import func

router = APIRouter()


@router.post("/", response_model=schemas.EventOut)
def create_event(event_in: schemas.EventCreate, db: Session = Depends(get_db)):
    event = Event(
        title=event_in.title,
        capacity=event_in.capacity,
        available_capacity=event_in.capacity,
        start_date=event_in.start_date,
        end_date=event_in.end_date,
        is_active=event_in.is_active,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.get("/{event_id}", response_model=schemas.EventOut)
def get_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    # Additional counts
    hold_count = db.query(func.count(Reservation.id)).filter(Reservation.event_id == event_id, Reservation.state == ReservationState.HOLD).scalar()
    confirmed_count = db.query(func.count(Reservation.id)).filter(Reservation.event_id == event_id, Reservation.state == ReservationState.CONFIRMED).scalar()
    # We return event, but client can infer counts from separate endpoint or we can extend schema; for now include in headers or separate field (left as improvement)
    return event
