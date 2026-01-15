import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timedelta

from app.main import app
from app.db import Base
import app.db as db_module
from app.tasks import cleanup_expired_holds
from app.models import ReservationState, Reservation

# --- Test Veritabanı Yapılandırması ---
@pytest.fixture(scope="module")
def test_engine():
    # In-memory SQLite için StaticPool kullanımı zorunludur (bağlantılar arası veri kaybını önler)
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return engine

@pytest.fixture(scope="module")
def session_local(test_engine):
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    # Uygulamanın kullandığı DB session fabrikasını test DB'sine yönlendiriyoruz
    db_module.engine = test_engine
    db_module.SessionLocal = SessionLocal
    yield SessionLocal

# --- Entegrasyon Testi ---
@pytest.mark.asyncio
async def test_full_reservation_flow(session_local):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        
        # 1. Kullanıcı Kaydı (Auth)
        r = await ac.post("/auth/register", json={"username": "alice", "password": "secret"})
        assert r.status_code == 200
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Etkinlik Oluşturma (Kapasite: 5)
        r = await ac.post("/events/", json={"title": "Concert", "capacity": 5}, headers=headers)
        assert r.status_code == 200
        event = r.json()
        event_id = event["id"]
        assert event["available_capacity"] == 5

        # 3. Sıralı olarak 5 Hold oluşturma (Kapasiteyi doldur)
        results = []
        for _ in range(5):
            resp = await ac.post("/reservations/hold", json={"event_id": event_id}, headers=headers)
            assert resp.status_code == 200
            results.append(resp)
        
        reservations = [r.json() for r in results]
        assert len(reservations) == 5

        # 4. Kapasite doluyken 6. talebin reddedildiğini doğrula
        r = await ac.post("/reservations/hold", json={"event_id": event_id}, headers=headers)
        assert r.status_code == 400

        # 5. İlk rezervasyonu CONFIRM et
        res_id = reservations[0]["id"]
        r = await ac.post(f"/reservations/confirm/{res_id}", headers=headers)
        assert r.status_code == 200
        assert r.json()["state"] == "CONFIRMED"

        # 6. Kapasitenin 0 olduğunu doğrula (1 Confirmed + 4 Hold = 5/5 Dolu)
        r = await ac.get(f"/events/{event_id}")
        assert r.json()["available_capacity"] == 0

        # 7. Kalan 4 HOLD'un süresini manuel olarak geçmişe al (Test amaçlı)
        db = session_local()
        try:
            now = datetime.utcnow()
            holds = db.query(Reservation).filter(
                Reservation.event_id == event_id, 
                Reservation.state == ReservationState.HOLD
            ).all()
            assert len(holds) == 4
            
            for h in holds:
                h.expires_at = now - timedelta(minutes=1)
            db.commit()

            # 8. KRİTİK DÜZELTME: Temizlik görevini test DB oturumuyla çalıştır
            # Bu işlem süresi dolan 4 kaydı silecek ve kapasiteyi 0'dan 4'ye çıkaracaktır.
            cleanup_expired_holds(db_session=db)

        finally:
            db.close()

        # 9. Kapasitenin iade edildiğini doğrula (Beklenen: 4)
        r = await ac.get(f"/events/{event_id}")
        evt = r.json()
        assert evt["available_capacity"] == 4
        
        # PDF İsteği: HOLD sayısının 0 olduğunu doğrula
        # (Önceki hat