from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db import get_db
from app.models import Event, Reservation, ReservationState
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

# --- Şemalar ---
class EventCreate(BaseModel):
    title: str
    capacity: int

# --- Endpointler ---

@router.post("/")  # Testin hata aldığı nokta burasıydı
def create_event(event_data: EventCreate, db: Session = Depends(get_db)):
    """Admin için etkinlik oluşturma endpoint'i"""
    new_event = Event(
        title=event_data.title,
        capacity=event_data.capacity,
        available_capacity=event_data.capacity,
        is_active=True
    )
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    return new_event

@router.get("/{event_id}")
def get_event_detail(event_id: int, db: Session = Depends(get_db)):
    """Etkinlik detaylarını ve kapasite durumunu döner"""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Etkinlik bulunamadı")
    
    # PDF isterleri: HOLD ve CONFIRMED sayılarını hesapla
    hold_count = db.query(Reservation).filter(
        Reservation.event_id == event_id,
        Reservation.state == ReservationState.HOLD
    ).count()
    
    confirmed_count = db.query(Reservation).filter(
        Reservation.event_id == event_id,
        Reservation.state == ReservationState.CONFIRMED
    ).count()
    
    return {
        "id": event.id,
        "title": event.title,
        "capacity": event.capacity,
        "available_capacity": event.available_capacity, #
        "hold_count": hold_count, #
        "confirmed_count": confirmed_count #
    }