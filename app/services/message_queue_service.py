import logging
import traceback

from aiogram.types import InlineKeyboardMarkup
from celery.result import AsyncResult

from app.celery_app import celery_app
from app.celery_tasks.telegram_tasks import (
    send_telegram_message as celery_send_telegram_message,
    send_bulk_messages as celery_send_bulk_messages,
    send_and_pin_telegram_message
)
from app.schemas import QueueResult, TaskStatus

logger = logging.getLogger(__name__)


class MessageQueueService:
    """
    Service for working with message queue through Celery.
    
    Methods:
        send_message: Add message to queue for sending
        send_and_pin_message: Add message to queue for sending and pinning
        send_bulk_messages: Add multiple messages to queue for sending
        get_task_status: Get task status
    """

    @staticmethod
    async def send_message(
            chat_id: int,
            text: str,
            parse_mode: str = 'HTML',
            message_id: int | None = None,
            message_thread_id: int | None = None,
            reply_markup: InlineKeyboardMarkup | None = None,
            disable_web_page_preview: bool = False
    ) -> QueueResult:
        """
        Add message to queue for sending.
        
        Args:
            chat_id (int): Chat ID
            text (str): Message text
            parse_mode (str): Parse mode
            message_id (int | None): If provided, reply to this message ID
            message_thread_id (int | None): Thread ID
            reply_markup (InlineKeyboardMarkup | None): Reply markup
            disable_web_page_preview (bool): Disable web page preview
        
        Returns:
            dict: Result of adding to queue
        """
        try:
            reply_markup_dict = reply_markup.model_dump() if reply_markup else None

            # Add task to Celery queue
            task: AsyncResult = celery_send_telegram_message.delay(
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode,
                message_id=message_id,
                message_thread_id=message_thread_id,
                reply_markup=reply_markup_dict,
                disable_web_page_preview=disable_web_page_preview,
            )

            logger.info('Message queued for chat %s, task ID: %s', chat_id, task.id)

            return QueueResult(
                status='queued',
                task_id=task.id,
                chat_id=chat_id
            )

        except Exception as e:
            logger.error('Error queuing message for chat %s: %s\n%s', chat_id, str(e), traceback.format_exc())
            return QueueResult(
                status='error',
                message=str(e),
                chat_id=chat_id
            )

    @staticmethod
    async def send_and_pin_message(
            chat_id: int,
            text: str,
            parse_mode: str = 'HTML',
            disable_web_page_preview: bool = False,
            message_id: int = None,
            message_thread_id: int = None,
            disable_pin_notification: bool = False
    ) -> QueueResult:
        """
        Add message to queue for sending and pinning.
        
        Args:
            chat_id (int): Chat ID
            text (str): Message text
            parse_mode (str): Parse mode
            disable_web_page_preview (bool): Disable web page preview
            message_id (int | None): If provided, reply to this message ID
            message_thread_id (int | None): Thread ID
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

            logger.info('Message queued for sending and pinning in chat %s, task ID: %s', chat_id, task.id)

            return QueueResult(
                status='queued',
                task_id=task.id,
                chat_id=chat_id
            )

        except Exception as e:
            logger.error('Error queuing send-and-pin message for chat %s: %s\n%s', chat_id, str(e),
                         traceback.format_exc())
            return QueueResult(
                status='error',
                message=str(e),
                chat_id=chat_id
            )

    @staticmethod
    async def send_bulk_messages(messages: list) -> QueueResult:
        """
        Add multiple messages to queue for sending.
        
        Args:
            messages (list): List of message dicts with keys: chat_id, text, parse_mode, disable_web_page_preview, message_id, message_thread_id

        Returns:
            dict: Result of adding to queue
        """
        try:
            task: AsyncResult = celery_send_bulk_messages.delay(messages)

            logger.info('Bulk messages queued, task ID: %s, count: %s', task.id, len(messages))

            return QueueResult(
                status='queued',
                task_id=task.id,
                message_count=len(messages)
            )

        except Exception as e:
            logger.error('Error queuing bulk messages: %s\n%s', str(e), traceback.format_exc())
            return QueueResult(
                status='error',
                message=str(e)
            )

    @staticmethod
    def get_task_status(task_id: str) -> TaskStatus:
        """
        Get task status.
        
        Args:
            task_id (str): Task ID
        
        Returns:
            dict: Task status and result if available
        """
        try:
            result: AsyncResult = celery_app.AsyncResult(task_id)

            return TaskStatus(
                task_id=task_id,
                status=result.status,
                result=result.result if result.ready() else None
            )

        except Exception as e:
            logger.error('Error getting task status for %s: %s', task_id, str(e))
            return TaskStatus(
                task_id=task_id,
                status='error',
                message=str(e)
            )
