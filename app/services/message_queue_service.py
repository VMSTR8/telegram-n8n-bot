import logging
from typing import Any

from celery.result import AsyncResult

from app.celery_app import celery_app
from app.celery_tasks.telegram_tasks import (
    send_telegram_message as celery_send_telegram_message,
    send_bulk_messages as celery_send_bulk_messages,
    send_and_pin_telegram_message
)

logger = logging.getLogger(__name__)


class MessageQueueService:
    """
    Service for working with message queue through Celery.

    Attributes:
        logger (logging.Logger): Logger instance for the service
    
    Methods:
        send_message: Add message to queue for sending
        send_and_pin_message: Add message to queue for sending and pinning
        send_bulk_messages: Add multiple messages to queue for sending
        get_task_status: Get task status
    """

    def __init__(self):
        self.logger = logger

    async def send_message(
            self,
            chat_id: int,
            text: str,
            parse_mode: str = 'HTML',
            disable_web_page_preview: bool = False,
            message_id: int = None,
            message_thread_id: int = None
    ) -> dict[str, Any]:
        """
        Add message to queue for sending.
        
        Args:
            chat_id (int): Chat ID
            text (str): Message text
            parse_mode (str): Parse mode
            disable_web_page_preview (bool): Disable web page preview
            message_id (int, optional): If provided, reply to this message ID
            message_thread_id (int, optional): Thread ID
        
        Returns:
            dict: Result of adding to queue
        """
        try:
            # Add task to Celery queue
            task: AsyncResult = celery_send_telegram_message.delay(
                chat_id=chat_id,
                message_thread_id=message_thread_id,
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

    async def send_and_pin_message(
            self,
            chat_id: int,
            text: str,
            parse_mode: str = 'HTML',
            disable_web_page_preview: bool = False,
            message_id: int = None,
            message_thread_id: int = None,
            disable_pin_notification: bool = False
    ) -> dict[str, Any]:
        """
        Add message to queue for sending and pinning.
        
        Args:
            chat_id (int): Chat ID
            text (str): Message text
            parse_mode (str): Parse mode
            disable_web_page_preview (bool): Disable web page preview
            message_id (int, optional): If provided, reply to this message ID
            message_thread_id (int, optional): Thread ID
            disable_pin_notification (bool): Disable pin notification
        
        Returns:
            dict: Result of adding to queue
        """
        try:

            task: AsyncResult = send_and_pin_telegram_message.delay(
                chat_id=chat_id,
                message_thread_id=message_thread_id,
                text=text,
                parse_mode=parse_mode,
                disable_web_page_preview=disable_web_page_preview,
                message_id=message_id,
                disable_pin_notification=disable_pin_notification
            )

            self.logger.info(f'Message queued for sending and pinning in chat {chat_id}, task ID: {task.id}')

            return {
                'status': 'queued',
                'task_id': task.id,
                'chat_id': chat_id
            }

        except Exception as e:
            self.logger.error(f'Error queuing send-and-pin message for chat {chat_id}: {e}')
            return {
                'status': 'error',
                'message': str(e),
                'chat_id': chat_id
            }

    async def send_bulk_messages(self, messages: list) -> dict[str, Any]:
        """
        Add multiple messages to queue for sending.
        
        Args:
            messages (list): List of message dicts with keys: chat_id, text, parse_mode, disable_web_page_preview, message_id, message_thread_id

        Returns:
            dict: Result of adding to queue
        """
        try:
            task: AsyncResult = celery_send_bulk_messages.delay(messages)

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

    def get_task_status(self, task_id: str) -> dict[str, Any]:
        """
        Get task status.
        
        Args:
            task_id (str): Task ID
        
        Returns:
            dict: Task status and result if available
        """
        try:
            result: AsyncResult = celery_app.AsyncResult(task_id)

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
