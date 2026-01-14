from celery import Celery
from app.config import settings

celery = Celery(__name__, broker=settings.REDIS_URL, backend=settings.REDIS_URL)

celery.conf.task_routes = {
    "app.tasks.*": {"queue": "default"}
}
