"""Celery worker package."""

from chaos_agent.workers.celery_app import celery_app

__all__ = ["celery_app"]
