import asyncio
import logging
import time
from asyncio import TimeoutError
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional, AsyncGenerator

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
    bot: Bot = Bot(token=settings.telegram.bot_token)
    try:
        yield bot
    finally:
        await bot.session.close()


def _handle_network_error(self, chat_id: int, e: Exception) -> Dict[str, Any]:
    """
    Handle network-related errors with exponential backoff retries.

    :param self: The task instance (for retrying)
    :param chat_id: Chat ID for logging
    :param e: The exception instance
    :return: Dict[str, Any] with error status if max retries exceeded
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
) -> Optional[Dict[str, Any]]:
    """
    Send a message to Telegram via Celery.
    
    :param chat_id: Chat ID
    :param text: Message text
    :param parse_mode: Parse mode (HTML, Markdown)
    :param disable_web_page_preview: Disable web page preview
    :param message_id: If provided, reply to this message ID
    :param message_thread_id: Thread ID for topics
    :return: Sending result
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
) -> Optional[Dict[str, Any]]:
    """
    Send a message to Telegram and pin it via Celery.

    :param chat_id: Chat ID
    :param text: Message text
    :param parse_mode: Parse mode (HTML, Markdown)
    :param disable_web_page_preview: Disable web page preview
    :param message_id: If provided, reply to this message ID
    :param message_thread_id: Thread ID for topics
    :param disable_pin_notification: If True, disable notification when pinning
    :return: Sending and pinning result
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
def ban_user_from_chat(self, chat_id: int, user_id: int) -> Optional[Dict[str, Any]]:
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
def send_bulk_messages(self, messages: list) -> List[Dict[str, Any]]:
    """
    Send multiple messages with controlled speed.
    
    :param messages: List of messages [{'chat_id': int, 'text': str}, ...]
    :return: Sending results
    """
    results: List[Dict[str, Any]] = []

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
