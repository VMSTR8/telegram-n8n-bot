import asyncio
import logging
import time
from asyncio import TimeoutError
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from aiogram import Bot
from aiogram.exceptions import TelegramRetryAfter, TelegramAPIError
from aiogram.types import Message
from aiohttp import ClientConnectionError, ClientError
from celery.result import AsyncResult

from app.celery_app import celery_app
from config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def bot_context() -> AsyncGenerator[Bot, None]:
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


def _handle_network_error(self, chat_id: int, e: Exception) -> dict[str, Any]:
    """
    Handle network-related errors with exponential backoff retries.

    Args:
        self: The task instance.
        chat_id: The chat ID where the error occurred.
        e: The exception that was raised.
    
    Raises:
        self.retry: Retries the task with exponential backoff.
    
    Returns:
        A dictionary with error status and message.
    """
    retry_count: int = self.request.retries
    retry_delay: int = min(300, (2 ** retry_count) * 10)
    logger.warning(
        f'Network error for chat {chat_id}: {e}. '
        f'Retry {retry_count + 1}/{self.max_retries} in {retry_delay}s'
    )
    if retry_count < self.max_retries:
        raise self.retry(countdown=retry_delay, exc=e)
    else:
        logger.error(f'Max retries exceeded for chat {chat_id}. Network error: {e}')
        return {'status': 'error', 'message': f'Network error after {self.max_retries} retries: {str(e)}'}


@celery_app.task(bind=True, max_retries=5, ignore_result=True)
def send_telegram_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: str = 'HTML',
        disable_web_page_preview: bool = False,
        message_id: int = None,
        message_thread_id: int = None
) -> dict[str, Any] | None:
    """
    Send a message to Telegram via Celery.
    
    Args:
        self: The task instance.
        chat_id: Chat ID
        text: Message text
        parse_mode: Parse mode (HTML, Markdown)
        disable_web_page_preview: Disable web page preview
        message_id: If provided, reply to this message ID
        message_thread_id: Thread ID for topics

    Raises:
        self.retry: Retries the task in case of rate limiting or network errors.
    
    Returns:
        A dictionary with sending status and message ID on success, or error details on failure.
    """

    async def _send_message():
        async with bot_context() as bot:
            send_result: Message = await bot.send_message(
                chat_id=chat_id,
                message_thread_id=message_thread_id,
                text=text,
                parse_mode=parse_mode,
                disable_web_page_preview=disable_web_page_preview,
                reply_to_message_id=message_id
            )

            return send_result

    try:
        result: Message = asyncio.run(_send_message())

        logger.info(f'Message sent successfully to chat {chat_id}')
        return {'status': 'success', 'message_id': result.message_id}

    except TelegramRetryAfter as e:
        # Handling 429 error - retry after specified time
        retry_after: int = e.retry_after
        logger.warning(f'Rate limit hit for chat {chat_id}. Retrying after {retry_after}s')

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
            logger.warning(f'Telegram API error for chat {chat_id}: {e}')
            return _handle_network_error(self, chat_id, ClientConnectionError(error_message))

    except Exception as e:
        logger.error(f'Unexpected error sending message to chat {chat_id}: {e}')
        return {'status': 'error', 'message': str(e)}


@celery_app.task(bind=True, max_retries=5, ignore_result=True)
def send_and_pin_telegram_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: str = 'HTML',
        disable_web_page_preview: bool = False,
        message_id: int = None,
        message_thread_id: int = None,
        disable_pin_notification: bool = False
) -> dict[str, Any] | None:
    """
    Send a message to Telegram and pin it via Celery.

    Args:
        self: The task instance.
        chat_id: Chat ID
        text: Message text
        parse_mode: Parse mode (HTML, Markdown)
        disable_web_page_preview: Disable web page preview
        message_id: If provided, reply to this message ID
        message_thread_id: Thread ID for topics
        disable_pin_notification: If True, pin without notification
    
    Raises:
        self.retry: Retries the task in case of rate limiting or network errors.
    
    Returns:
        A dictionary with sending and pinning status and message ID on success, or error details on failure.
    """

    async def _send_and_pin():
        async with bot_context() as bot:
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

        logger.info(f'Message sent and pinned successfully to chat {chat_id}')
        return {'status': 'success', 'message_id': result.message_id}

    except TelegramRetryAfter as e:
        retry_after: int = e.retry_after
        logger.warning(f'Rate limit hit for chat {chat_id}. Retrying after {retry_after}s')

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
        logger.error(f'Unexpected error sending message to chat {chat_id}: {e}')
        return {'status': 'error', 'message': str(e)}


@celery_app.task(bind=True, max_retries=3, ignore_result=True)
def ban_user_from_chat(self, chat_id: int, user_id: int) -> dict[str, Any] | None:
    """
    Ban a user from a Telegram chat via Celery.
    
    Args:
        self: The task instance.
        chat_id: Chat ID
        user_id: User ID to ban
    
    Raises:
        self.retry: Retries the task in case of rate limiting or network errors.
    
    Returns:
        A dictionary with banning status on success, or error details on failure.
    """
    try:
        async def _ban_user():
            async with bot_context() as bot:
                await bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
                logger.info(f'User {user_id} banned from chat {chat_id}')

        asyncio.run(_ban_user())
        return {'status': 'success', 'detail': f'User {user_id} banned from chat {chat_id}'}

    except TelegramRetryAfter as e:
        retry_after: int = e.retry_after
        logger.warning(f'Rate limit hit for chat {chat_id}. Retrying after {retry_after}s')

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
        logger.error(f'Error banning user {user_id} from chat {chat_id}: {e}')
        return {'status': 'error', 'message': str(e)}


@celery_app.task(bind=True, max_retries=3, ignore_result=True)
def send_bulk_messages(self, messages: list) -> list[dict[str, Any]]:
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
        A list of dictionaries with sending status for each message.
    """
    results: list[dict[str, Any]] = []

    for i, message_data in enumerate(messages):
        try:
            result: AsyncResult = send_telegram_message.delay(
                chat_id=message_data['chat_id'],
                text=message_data['text'],
                parse_mode=message_data.get('parse_mode', 'HTML'),
                disable_web_page_preview=message_data.get('disable_web_page_preview', False),
                message_id=message_data.get('message_id'),
                message_thread_id=message_data.get('message_thread_id')
            )
            results.append(result.get())

            if i < len(messages) - 1:
                time.sleep(0.1)

        except Exception as e:
            logger.error(f'Error in bulk send: {e}')
            results.append({'status': 'error', 'message': str(e)})

    return results
