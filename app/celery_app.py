import os

from celery import Celery

from config import settings

celery_app = Celery('telegram_bot')

celery_app.conf.update(
    broker_url=os.getenv('RABBITMQ_URL'),  # TODO: i'll add settings link later
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

"""
Explicitly import tasks.
For some reason, autodiscover_tasks is not working.
So we need to explicitly import tasks.
Why? I don't know (lol)
And yes - I know that it's not a good practice to import tasks here.
But once more time - it's working!
"""
from app.celery_tasks import message_tasks
