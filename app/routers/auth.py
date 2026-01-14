from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import schemas, auth
from app.db import get_db
from app.models import User
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

router = APIRouter()


@router.post("/register", response_model=schemas.Token)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == user_in.username).first()
    if user:
        raise HTTPException(status_code=400, detail="Username already registered")
    user = User(username=user_in.username, hashed_password=auth.get_password_hash(user_in.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    token = auth.create_access_token(user.username, expires_delta=timedelta(minutes=60))
    return {"access_token": token}


@router.post("/token", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    token = auth.create_access_token(user.username, expires_delta=timedelta(minutes=60))
    return {"access_token": token}
