from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db import Base
import enum


class ReservationState(str, enum.Enum):
    HOLD = "HOLD"
    CONFIRMED = "CONFIRMED"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)


class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    capacity = Column(Integer, nullable=False)
    available_capacity = Column(Integer, nullable=False)
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    reservations = relationship("Reservation", back_populates="event")


class Reservation(Base):
    __tablename__ = "reservations"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    state = Column(Enum(ReservationState), nullable=False, default=ReservationState.HOLD)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
    event = relationship("Event", back_populates="reservations")
