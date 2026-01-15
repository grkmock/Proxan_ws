from fastapi import FastAPI
from app.routers import events, reservations, auth
from apscheduler.schedulers.background import BackgroundScheduler
from app.tasks import cleanup_expired_holds
from contextlib import asynccontextmanager

# --- Scheduler Ayarları ---
# Uygulama başladığında çalışacak ve kapandığında duracak şekilde yapılandırıyoruz
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Uygulama başlarken scheduler'ı başlat
    scheduler = BackgroundScheduler()
    # Her 1 dakikada bir süresi dolan hold kayıtlarını temizle ve kapasiteyi iade et [cite: 39, 41]
    scheduler.add_job(cleanup_expired_holds, 'interval', minutes=1)
    scheduler.start()
    yield
    # Uygulama kapanırken scheduler'ı güvenli bir şekilde kapat
    scheduler.shutdown()

app = FastAPI(
    title="Proxan - Reservation System",
    lifespan=lifespan
)

# Routerlar
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(events.router, prefix="/events", tags=["events"])
app.include_router(reservations.router, prefix="/reservations", tags=["reservations"])

@app.get("/health")
def health():
    return {"status": "ok"}