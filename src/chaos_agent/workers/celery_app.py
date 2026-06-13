"""Celery application — broker, task routing."""

from celery import Celery

celery_app = Celery("chaos_agent")
celery_app.conf.broker_url = "redis://localhost:6379/1"
celery_app.conf.result_backend = "redis://localhost:6379/2"
