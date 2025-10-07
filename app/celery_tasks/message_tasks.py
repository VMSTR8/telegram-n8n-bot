import logging
import asyncio
from typing import Dict, Any, List

from asyncio import TimeoutError
from aiohttp import ClientConnectionError, ClientError

from aiogram import Bot
from aiogram.exceptions import TelegramRetryAfter, TelegramAPIError
from aiogram.types import Message

from app.celery_app import celery_app
from config import settings

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=5, ignore_result=True)
def send_telegram_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: str = 'HTML',
        disable_web_page_preview: bool = False,
        message_id: int = None
) -> Dict[str, Any]:
    """
    Send a message to Telegram via Celery.
    
    :param chat_id: Chat ID
    :param text: Message text
    :param parse_mode: Parse mode (HTML, Markdown)
    :param disable_web_page_preview: Disable web page preview
    :param message_id: If provided, reply to this message ID
    :return: Sending result
    """
    try:
        bot_token = settings.telegram.bot_token
        if not bot_token:
            logger.error('Bot token not found in environment!')
            return {'status': 'error', 'message': 'Bot token not found'}

        bot = Bot(token=bot_token)

        async def _send_message():
            try:
                result = await bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode=parse_mode,
                    disable_web_page_preview=disable_web_page_preview,
                    reply_to_message_id=message_id
                )
                return result
            finally:
                await bot.session.close()

        result = asyncio.run(_send_message())

        logger.info(f'Message sent successfully to chat {chat_id}')
        return {'status': 'success', 'message_id': result.message_id}

    except TelegramRetryAfter as e:
        # Handling 429 error - retry after specified time
        retry_after = e.retry_after
        logger.warning(f'Rate limit hit for chat {chat_id}. Retrying after {retry_after}s')

        # Retry task after retry_after seconds
        raise self.retry(countdown=retry_after, max_retries=5)
    
    except (ClientConnectionError, TimeoutError, ClientError) as e:
        retry_count = self.request.retries
        retry_delay = min(300, (2 ** retry_count) * 10)
        logger.warning(
            f'Network error for chat {chat_id}: {e}. '
            f'Retry {retry_count + 1}/{self.max_retries} in {retry_delay}s'
        )

        if retry_count < self.max_retries:
            raise self.retry(countdown=retry_delay, exc=e)
        else:
            logger.error(f'Max retries exceeded for chat {chat_id}. Network error: {e}')
            return {'status': 'error', 'message': f'Network error after {self.max_retries} retries: {str(e)}'}

    except TelegramAPIError as e:
        # Other Telegram API errors
        logger.error(f'Telegram API error for chat {chat_id}: {e}')
        return {'status': 'error', 'message': str(e)}

    except Exception as e:
        # Unexpected errors
        logger.error(f'Unexpected error sending message to chat {chat_id}: {e}')
        return {'status': 'error', 'message': str(e)}


# this task MAY BE used in future
# or may be not
@celery_app.task(bind=True, max_retries=3, ignore_result=True)
def send_bulk_messages(self, messages: list) -> List[Dict[str, Any]]:
    """
    Send multiple messages with controlled speed.
    
    :param messages: List of messages [{'chat_id': int, 'text': str}, ...]
    :return: Sending results
    """
    results = []

    for i, message_data in enumerate(messages):
        try:
            # Send message
            result = send_telegram_message.delay(
                chat_id=message_data['chat_id'],
                text=message_data['text'],
                parse_mode=message_data.get('parse_mode', 'HTML'),
                disable_web_page_preview=message_data.get('disable_web_page_preview', False)
            )
            results.append(result.get())

            # Small delay between messages (0.1 seconds)
            if i < len(messages) - 1:  # Don't wait after last message
                import time
                time.sleep(0.1)

        except Exception as e:
            logger.error(f'Error in bulk send: {e}')
            results.append({'status': 'error', 'message': str(e)})

    return results
