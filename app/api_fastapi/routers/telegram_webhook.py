import logging
import traceback
from typing import Any

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramNetworkError
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
) -> dict[str, str] | None:
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
    try:
        update_data: dict[str, Any] = await request.json()
        update = Update(**update_data)
        await dispatcher.feed_update(bot, update)
        return {'status': 'ok'}

    except TelegramNetworkError as tne:
        logger.error('Telegram network error: %s', str(tne))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='Service Unavailable due to Telegram network issues.') from tne

    except Exception as e:
        logger.error('Error processing Telegram update: %s\n%s', str(e), traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Internal Server Error while processing Telegram update.') from e


@telegram_webhook_router.get(path='/webhook/health', response_model=dict[str, str])
async def health_check() -> dict[str, str]:
    """
    Health check endpoint to verify the webhook is operational.
    
    Returns:
        A dictionary indicating the health status of the webhook.
    """
    return {'status': 'healthy', 'message': 'Webhook is operational. Bye, have a great time!'}
