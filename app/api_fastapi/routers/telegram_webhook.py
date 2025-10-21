import logging
import traceback
from typing import Any

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramNetworkError, TelegramBadRequest
from aiogram.types import Update
from fastapi import APIRouter, Request, HTTPException, Depends, status

from app.api_fastapi.dependencies import (
    get_bot,
    get_dispatcher
)
from app.decorators import FastAPIValidate

logger = logging.getLogger(__name__)
telegram_webhook_router: APIRouter = APIRouter()


@telegram_webhook_router.post(path='/webhook', response_model=dict[str, str])
@FastAPIValidate.validate_header_secret()
async def telegram_webhook(
        request: Request,
        bot: Bot = Depends(get_bot),
        dispatcher: Dispatcher = Depends(get_dispatcher),
) -> dict[str, str]:
    """
    Endpoint to handle incoming Telegram webhook updates.

    Args:
        request (Request): FastAPI request object containing the update data.
        bot (Bot): Instance of the Telegram Bot.
        dispatcher (Dispatcher): Instance of the Dispatcher to process updates.

    Raises:
        HTTPException: If there is an error processing the update.

    Returns:
        Acknowledgment of successful processing.
    """
    update_data: dict[str, Any] | None = None

    try:
        update_data: dict[str, Any] = await request.json()
        update = Update(**update_data)
        await dispatcher.feed_update(bot, update)
        return {'status': 'ok'}

    except TelegramBadRequest as tbr:
        logger.warning(
            'Telegram bad request: %s | Update: %s',
            str(tbr),
            update_data.get('update_id', 'unknown') if update_data else 'unknown'
        )
        return {'status': 'ok', 'warning': 'Handled bad request.'}

    except TelegramNetworkError as tne:
        logger.error(
            'Telegram network error: %s | Update: %s',
            str(tne),
            update_data.get('update_id', 'unknown') if update_data else 'unknown'
        )
        return {'status': 'ok', 'message': 'Network error, try again later.'}

    except ValueError as ve:
        logger.error('Invalid update data: %s\n%s', str(ve), traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid update data format.'
        ) from ve

    except Exception as e:
        logger.error(
            'Unexpected error processing update: %s | Upadate: %s\n%s',
            str(e),
            update_data.get('update_id', 'unknown') if update_data else 'unknown',
            traceback.format_exc()
        )
        return {'status': 'ok', 'message': 'An unexpected error occurred.'}


@telegram_webhook_router.get(path='/webhook/health', response_model=dict[str, str])
async def health_check() -> dict[str, str]:
    """
    Health check endpoint to verify the webhook is operational.
    
    Returns:
        A dictionary indicating the health status of the webhook.
    """
    return {'status': 'healthy', 'message': 'Webhook is operational. Bye, have a great time!'}
