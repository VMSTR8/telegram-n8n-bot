import asyncio
import logging
import time
import traceback
from asyncio import TimeoutError
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from aiogram import Bot
from aiogram.exceptions import TelegramRetryAfter, TelegramAPIError
from aiogram.types import Message, InlineKeyboardMarkup
from aiohttp import ClientConnectionError, ClientError
from celery.result import AsyncResult

from app.celery_app import celery_app
from app.schemas import TaskResponse
from config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def _bot_context() -> AsyncGenerator[Bot, None]:
    """
    Asynchronous context manager to create and close a Bot instance.

    Yields:
        An instance of Bot.
    
    Finally:
        Closes the bot session.

    Returns:
        Instance of Bot.
    """
    bot: Bot = Bot(token=settings.telegram.bot_token)
    try:
        yield bot
    finally:
        await bot.session.close()


def _handle_network_error(self, chat_id: int, e: Exception) -> TaskResponse:
    """
    Handle network-related errors with exponential backoff retries.

    Args:
        self: The task instance.
        chat_id: The chat ID where the error occurred.
        e: The exception that was raised.
    
    Raises:
        self.retry: Retries the task with exponential backoff.
    
    Returns:
        A TaskResponse object with error status and message.
    """
    retry_count: int = self.request.retries
    retry_delay: int = min(300, (2 ** retry_count) * 10)
    logger.warning(
        'Network error for chat %s: %s. Retry %d/%d in %d seconds',
        chat_id, str(e), retry_count + 1, self.max_retries, retry_delay
    )
    if retry_count < self.max_retries:
        raise self.retry(countdown=retry_delay, exc=e)
    else:
        logger.error('Max retries exceeded for chat %s. Network error: %s', chat_id, str(e))
        return TaskResponse(status='error', message=f'Network error after {self.max_retries} retries: {str(e)}')


@celery_app.task(bind=True, max_retries=5, ignore_result=True)
def send_telegram_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: str = 'HTML',
        message_id: int | None = None,
        message_thread_id: int | None = None,
        reply_markup: dict | None = None,
        disable_web_page_preview: bool = False
) -> TaskResponse | None:
    """
    Send a message to Telegram via Celery.
    
    Args:
        self: The task instance
        chat_id (int): Chat ID
        text (str): Message text
        parse_mode (str): Parse mode (HTML, Markdown)
        message_id (int | None): If provided, reply to this message ID
        message_thread_id (int | None): Thread ID for topics
        reply_markup (dict | None): Reply markup as a dictionary
        disable_web_page_preview (bool): Disable web page preview

    Raises:
        self.retry: Retries the task in case of rate limiting or network errors.
    
    Returns:
        A TaskResponse object with sending status and message ID on success, or error details on failure.
    """

    async def _send_message():
        reply_markup_obj: InlineKeyboardMarkup | None = None

        if reply_markup:
            reply_markup_obj = InlineKeyboardMarkup.model_validate(reply_markup)

        async with _bot_context() as bot:
            send_result: Message = await bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode,
                reply_to_message_id=message_id,
                message_thread_id=message_thread_id,
                reply_markup=reply_markup_obj,
                disable_web_page_preview=disable_web_page_preview
            )

            return send_result

    try:
        result: Message = asyncio.run(_send_message())

        logger.info('Message sent successfully to chat %s, message ID: %s', chat_id, result.message_id)
        return TaskResponse(status='success', message_id=result.message_id)

    except TelegramRetryAfter as e:
        # Handling 429 error - retry after specified time
        retry_after: int = e.retry_after
        logger.warning('Rate limit hit for chat %s. Retrying after %d seconds', chat_id, retry_after)

        # Retry task after retry_after seconds
        raise self.retry(countdown=retry_after, max_retries=5)

    except (ClientConnectionError, TimeoutError, ClientError) as e:
        return _handle_network_error(self, chat_id, e)

    except TelegramAPIError as e:
        error_message: str = str(e)
        if any(
                keyword in error_message.lower() for keyword in [
                    'cannot connect', 'connection', 'timeout', 'network'
                ]
        ):
            logger.warning('Telegram API error for chat %s: %s', chat_id, str(e))
            return _handle_network_error(self, chat_id, ClientConnectionError(error_message))

    except Exception as e:
        logger.error('Unexpected error sending message to chat %s: %s\n%s', chat_id, str(e), traceback.format_exc())
        return TaskResponse(status='error', message=str(e))


@celery_app.task(bind=True, max_retries=5, ignore_result=True)
def send_and_pin_telegram_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: str = 'HTML',
        message_id: int = None,
        message_thread_id: int = None,
        disable_web_page_preview: bool = False,
        disable_pin_notification: bool = False
) -> TaskResponse | None:
    """
    Send a message to Telegram and pin it via Celery.

    Args:
        self: The task instance
        chat_id (int): Chat ID
        text (str): Message text
        parse_mode (str): Parse mode (HTML, Markdown)
        message_id (int | None): If provided, reply to this message ID
        message_thread_id (int | None): Thread ID for topics
        disable_web_page_preview (bool): Disable web page preview
        disable_pin_notification (bool): Disable notification for pinning the message
    
    Raises:
        self.retry: Retries the task in case of rate limiting or network errors.
    
    Returns:
        A dictionary with sending and pinning status and message ID on success, or error details on failure.
    """

    async def _send_and_pin():
        async with _bot_context() as bot:
            send_result: Message = await bot.send_message(
                chat_id=chat_id,
                message_thread_id=message_thread_id,
                text=text,
                parse_mode=parse_mode,
                disable_web_page_preview=disable_web_page_preview,
                reply_to_message_id=message_id
            )

            await bot.pin_chat_message(
                chat_id=chat_id,
                message_id=send_result.message_id,
                disable_notification=disable_pin_notification
            )

            return send_result

    try:
        result: Message = asyncio.run(_send_and_pin())

        logger.info('Message sent and pinned successfully to chat %s', chat_id)
        return TaskResponse(status='success', message_id=result.message_id)

    except TelegramRetryAfter as e:
        retry_after: int = e.retry_after
        logger.warning('Rate limit hit for chat %s. Retrying after %d seconds', chat_id, retry_after)

        raise self.retry(countdown=retry_after, max_retries=5)

    except (ClientConnectionError, TimeoutError, ClientError) as e:
        return _handle_network_error(self, chat_id, e)

    except TelegramAPIError as e:
        error_message: str = str(e)
        if any(
                keyword in error_message.lower() for keyword in [
                    'cannot connect', 'connection', 'timeout', 'network'
                ]
        ):
            logger.warning('Telegram API error for chat %s: %s', chat_id, str(e))
            return _handle_network_error(self, chat_id, ClientConnectionError(error_message))

    except Exception as e:
        logger.error(
            'Unexpected error sending message to chat %s: %s\n%s', chat_id, str(e), traceback.format_exc()
        )
        return TaskResponse(status='error', message=str(e))


@celery_app.task(bind=True, max_retries=3, ignore_result=True)
def ban_user_from_chat(self, chat_id: int, user_id: int) -> TaskResponse | None:
    """
    Ban a user from a Telegram chat via Celery.
    
    Args:
        self: The task instance.
        chat_id: Chat ID
        user_id: User ID to ban
    
    Raises:
        self.retry: Retries the task in case of rate limiting or network errors.
    
    Returns:
        A TaskResponse object with banning status on success, or error details on failure.
    """
    try:
        async def _ban_user():
            async with _bot_context() as bot:
                await bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
                logger.info(f'User {user_id} banned from chat {chat_id}')

        asyncio.run(_ban_user())
        return TaskResponse(status='success', detail=f'User {user_id} banned from chat {chat_id}')

    except TelegramRetryAfter as e:
        retry_after: int = e.retry_after
        logger.warning('Rate limit hit for chat %s. Retrying after %d seconds', chat_id, retry_after)

        raise self.retry(countdown=retry_after, max_retries=5)

    except (ClientConnectionError, TimeoutError, ClientError) as e:
        return _handle_network_error(self, chat_id, e)

    except TelegramAPIError as e:
        error_message: str = str(e)
        if any(
                keyword in error_message.lower() for keyword in [
                    'cannot connect', 'connection', 'timeout', 'network'
                ]
        ):
            logger.warning(f'Telegram API error for chat {chat_id}: {e}')
            return _handle_network_error(self, chat_id, ClientConnectionError(error_message))

    except Exception as e:
        logger.error(
            'Error banning user %s from chat %s: %s\n%s', user_id, chat_id, str(e), traceback.format_exc()
        )
        return TaskResponse(status='error', message=str(e))


@celery_app.task(bind=True, max_retries=3, ignore_result=True)
def send_bulk_messages(self, messages: list) -> list[TaskResponse]:
    """
    Send multiple messages with controlled speed.
    
    Args:
        self: The task instance.
        messages: List of message data dictionaries, each containing:
            - chat_id: Chat ID
            - text: Message text
            - parse_mode: Parse mode (HTML, Markdown) [optional]
            - disable_web_page_preview: Disable web page preview [optional]
            - message_id: If provided, reply to this message ID [optional]
            - message_thread_id: Thread ID for topics [optional]
    
    Returns:
        A list of TaskResponse objects with sending status for each message.
    """
    results: list[TaskResponse] = []

    for i, message_data in enumerate(messages):
        try:
            result: AsyncResult = send_telegram_message.delay(
                chat_id=message_data['chat_id'],
                text=message_data['text'],
                parse_mode=message_data.get('parse_mode', 'HTML'),
                message_id=message_data.get('message_id'),
                message_thread_id=message_data.get('message_thread_id'),
                disable_web_page_preview=message_data.get('disable_web_page_preview', False)
            )

            task_result = result.get()
            if isinstance(task_result, dict):
                results.append(TaskResponse(**task_result))
            else:
                results.append(task_result)

            if i < len(messages) - 1:
                time.sleep(1)

        except Exception as e:
            logger.error('Error in bulk send for message %d: %s\n%s', i, str(e), traceback.format_exc())
            results.append(TaskResponse(status='error', message=str(e)))

    return results
