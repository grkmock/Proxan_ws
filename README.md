# Proxan - Backend Developer Case Study

<!-- Replace OWNER and REPO in the line below with your GitHub owner and repo to enable the badge -->
[![CI](https://github.com/grkmock/Proxan_ws/actions/workflows/ci.yml/badge.svg)](https://github.com/grkmock/Proxan_ws/actions/workflows/ci.yml)

Scaffold for the reservation system (HOLD -> CONFIRM) using FastAPI, PostgreSQL, Redis and Celery.

Quick start (development):

1. Copy `.env.example` to `.env` and edit if needed.
2. Start services: `docker compose up --build`
3. Create DB tables using Alembic (inside web container): `alembic upgrade head` (configure sqlalchemy.url in alembic.ini or env vars)

What's included:
- FastAPI app with basic auth (JWT)
- Models: User, Event (with available_capacity), Reservation
- Celery worker and a cleanup task to remove expired HOLDs

Continuous Integration:
- GitHub Actions workflow `ci.yml` runs migrations and tests on push/PR.

Next steps:
- Add migrations
- Add integration tests
- Add Postman collection and README usage examples
- Harden auth & add admin-only checks for event creation
