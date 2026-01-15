import pytest
import sys
import os
from datetime import datetime, timedelta
from types import SimpleNamespace
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

# Proje kök dizinini Python yoluna ekleyerek 'app' modülünün her ortamda bulunmasını sağlar
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models import Base, Event, Reservation, ReservationState
from app.main import app
from app.db import get_db

# Auth bypass için dependency'yi yakalıyoruz
try:
    from app.routers.reservations import get_current_user
except ImportError:
    get_current_user = None

# --- SQLite In-Memory Konfigürasyonu ---
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- Async Test Desteği ---
@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="function")
def db():
    """Her test için izole, temiz bir veritabanı ve başlangıç verisi oluşturur."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    
    # Testlerin genelinde kullanılan varsayılan Etkinlik (ID: 1)
    if not session.query(Event).filter(Event.id == 1).first():
        test_event = Event(
            id=1,
            title="Test Etkinliği",
            capacity=100,
            available_capacity=100,
            start_date=datetime.utcnow() + timedelta(days=1),
            end_date=datetime.utcnow() + timedelta(days=2),
            is_active=True
        )
        session.add(test_event)
        session.commit()
    
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    """FastAPI bağımlılıklarını test nesneleriyle (DB ve Mock Auth) değiştirir."""
    app.dependency_overrides[get_db] = lambda: db
    
    if get_current_user:
        # AttributeError'u engelleyen ve current_user.id'ye erişim sağlayan yapı
        mock_user = SimpleNamespace(id=1, username="testuser")
        app.dependency_overrides[get_current_user] = lambda: mock_user
    
    with TestClient(app) as c:
        yield c
    
    app.dependency_overrides.clear()

@pytest.fixture
def hold_reservation(db):
    """Onaylama testleri için 'HOLD' durumunda hazır rezervasyon."""
    res = Reservation(
        id=1, event_id=1, user_id=1, 
        state=ReservationState.HOLD, 
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    db.add(res)
    db.commit()
    db.refresh(res)
    return res

@pytest.fixture
def expired_hold(db):
    """Süre aşımı senaryoları için süresi dolmuş rezervasyon."""
    res = Reservation(
        id=2, event_id=1, user_id=1, 
        state=ReservationState.HOLD, 
        expires_at=datetime.utcnow() - timedelta(minutes=10)
    )
    db.add(res)
    db.commit()
    db.refresh(res)
    return res