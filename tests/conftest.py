import pytest
from datetime import datetime, timedelta
from types import SimpleNamespace
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

# Uygulama ve Model importları
from app.models import Base, Event, Reservation, ReservationState
from app.main import app
from app.db import get_db

# Auth bypass için dependency'yi yakalıyoruz
try:
    from app.routers.reservations import get_current_user
except ImportError:
    get_current_user = None

# --- SQLite In-Memory Konfigürasyonu ---
# Testlerin izole ve hızlı olması için bellekte (RAM) çalışan SQLite kullanıyoruz.
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    """Her test için temiz bir veritabanı ve başlangıç verisi oluşturur."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    
    # Testler için zorunlu olan Event (ID: 1) verisi
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
    """FastAPI bağımlılıklarını (DB ve Auth) test nesneleriyle değiştirir."""
    # Veritabanı bağlantısını override et
    app.dependency_overrides[get_db] = lambda: db
    
    # Kullanıcı kimlik doğrulamasını bypass et (SimpleNamespace ile)
    if get_current_user:
        mock_user = SimpleNamespace(id=1, username="testuser")
        app.dependency_overrides[get_current_user] = lambda: mock_user
    
    with TestClient(app) as c:
        yield c
    
    # Test bittiğinde override'ları temizle
    app.dependency_overrides.clear()

@pytest.fixture
def hold_reservation(db):
    """Onaylama testleri için geçerli bir 'HOLD' durumunda rezervasyon."""
    res = Reservation(
        id=1,
        event_id=1,
        user_id=1,
        state=ReservationState.HOLD,
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    db.add(res)
    db.commit()
    db.refresh(res)
    return res

@pytest.fixture
def expired_hold(db):
    """Süre kontrolü testi için geçmiş tarihli bir rezervasyon."""
    res = Reservation(
        id=2,
        event_id=1,
        user_id=1,
        state=ReservationState.HOLD,
        expires_at=datetime.utcnow() - timedelta(minutes=10)
    )
    db.add(res)
    db.commit()
    db.refresh(res)
    return res