from celery import Celery

from config import settings

celery_app: Celery = Celery('telegram_bot')

celery_app.conf.update(
    broker_url=settings.rabbitmq.url,
    result_backend='rpc://',

    # Settings for task serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',

    # Settings for timezone
    timezone=settings.timezone,
    enable_utc=True,

    # Settings for handling 429 errors (rate limit)
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
)

celery_app.autodiscover_tasks(['app.celery_tasks'])
