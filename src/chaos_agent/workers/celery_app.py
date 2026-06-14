"""Celery application — broker, task routing."""

from celery import Celery

celery_app = Celery("chaos_agent")


def configure_celery() -> None:
    from chaos_agent.config import get_settings

    settings = get_settings()
    celery_app.conf.broker_url = settings.celery_broker_url
    celery_app.conf.result_backend = settings.redis_url
    celery_app.conf.task_default_queue = "chaos_agent"


configure_celery()

# Register tasks
import chaos_agent.workers.tasks  # noqa: E402, F401
