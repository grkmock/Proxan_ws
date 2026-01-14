from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models import ReservationState


class UserCreate(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class EventCreate(BaseModel):
    title: str
    capacity: int
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    is_active: Optional[bool] = True


class EventOut(BaseModel):
    id: int
    title: str
    capacity: int
    available_capacity: int
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    is_active: bool

    class Config:
        orm_mode = True


class ReservationCreate(BaseModel):
    event_id: int


class ReservationOut(BaseModel):
    id: int
    user_id: int
    event_id: int
    state: ReservationState
    expires_at: Optional[datetime]
    created_at: datetime

    class Config:
        orm_mode = True
