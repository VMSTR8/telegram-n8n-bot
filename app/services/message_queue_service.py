import logging
from typing import Dict, Any

from app.celery_app import celery_app
from app.celery_tasks.message_tasks import (
    send_telegram_message as celery_send_telegram_message,
    send_bulk_messages as celery_send_bulk_messages
)

logger = logging.getLogger(__name__)


class MessageQueueService:
    """
    Service for working with message queue through Celery.
    """

    def __init__(self):
        self.logger = logger

    async def send_message(
            self,
            chat_id: int,
            text: str,
            parse_mode: str = 'HTML',
            disable_web_page_preview: bool = False,
            message_id: int = None
    ) -> Dict[str, Any]:
        """
        Add message to queue for sending.
        
        :param chat_id: Chat ID
        :param text: Message text
        :param parse_mode: Parse mode
        :param disable_web_page_preview: Disable web page preview
        :param message_id: If provided, reply to this message ID
        :return: Result of adding to queue
        """
        try:
            # Add task to Celery queue
            task = celery_send_telegram_message.delay(
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode,
                disable_web_page_preview=disable_web_page_preview,
                message_id=message_id
            )

            self.logger.info(f'Message queued for chat {chat_id}, task ID: {task.id}')

            return {
                'status': 'queued',
                'task_id': task.id,
                'chat_id': chat_id
            }

        except Exception as e:
            self.logger.error(f'Error queuing message for chat {chat_id}: {e}')
            return {
                'status': 'error',
                'message': str(e),
                'chat_id': chat_id
            }

    async def send_bulk_messages(self, messages: list) -> Dict[str, Any]:
        """
        Add multiple messages to queue for sending.
        
        :param messages: List of messages
        :return: Result of adding to queue
        """
        try:
            task = celery_send_bulk_messages.delay(messages)

            self.logger.info(f'Bulk messages queued, task ID: {task.id}, count: {len(messages)}')

            return {
                'status': 'queued',
                'task_id': task.id,
                'message_count': len(messages)
            }

        except Exception as e:
            self.logger.error(f'Error queuing bulk messages: {e}')
            return {
                'status': 'error',
                'message': str(e)
            }

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get task status.
        
        :param task_id: Task ID
        :return: Task status
        """
        try:
            result = celery_app.AsyncResult(task_id)

            return {
                'task_id': task_id,
                'status': result.status,
                'result': result.result if result.ready() else None
            }

        except Exception as e:
            self.logger.error(f'Error getting task status for {task_id}: {e}')
            return {
                'task_id': task_id,
                'status': 'error',
                'message': str(e)
            }
