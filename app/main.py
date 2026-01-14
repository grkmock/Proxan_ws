from fastapi import FastAPI
from app.routers import events, reservations, auth

app = FastAPI(title="Proxan - Reservation System")

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(events.router, prefix="/events", tags=["events"])
app.include_router(reservations.router, prefix="/reservations", tags=["reservations"])


@app.get("/health")
def health():
    return {"status": "ok"}
