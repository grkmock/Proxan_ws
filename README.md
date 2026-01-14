# Proxan Backend Case Study

This project implements a **two-phase reservation system (HOLD → CONFIRM)**  
designed to handle concurrency, background jobs, and transactional integrity.

---

## Tech Stack
- Python 3.10
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Redis
- Celery
- Docker & Docker Compose
- Pytest

---

## System Overview

Reservation flow consists of two steps:

1. **HOLD**
   - Temporarily reserves capacity for 5 minutes
   - Stored with status = HOLD
   - Capacity is decreased temporarily

2. **CONFIRM**
   - Must be done within 5 minutes
   - HOLD → CONFIRMED
   - Capacity becomes permanent

Expired HOLDs are cleaned automatically by a **Celery background worker**.

---

## Architecture

- Web API: FastAPI
- Background Jobs: Celery + Redis
- Database: PostgreSQL
- Concurrency control: DB transactions & row locking
- CI: GitHub Actions (migration + tests)

---

## Environment Variables

```env
DATABASE_URL=postgresql+psyc_
