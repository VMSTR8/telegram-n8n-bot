import logging
from typing import Dict, Any

from aiogram import Bot, Dispatcher
from aiogram.types import Update
from fastapi import APIRouter, Request, HTTPException, Depends

from app.api_fastapi.dependencies import (
    get_bot,
    get_dispatcher
)
from app.decorators import FastAPIValidate

telegram_webhook_router = APIRouter()


@telegram_webhook_router.post(path='/webhook', response_model=Dict[str, str])
@FastAPIValidate.validate_header_secret()
async def telegram_webhook(
        request: Request,
        bot: Bot = Depends(get_bot),
        dispatcher: Dispatcher = Depends(get_dispatcher),
) -> Dict[str, str]:
    """
    Endpoint to handle incoming Telegram webhook updates.

    :param request: Request - FastAPI request object containing the update data.
    :param bot: Bot - instance of the Telegram Bot.
    :param dispatcher: Dispatcher - instance of the Dispatcher to process updates.
    :return: Dict[str, str] - Acknowledgment of successful processing.
    """
    try:
        update_data: Dict[str, Any] = await request.json()
        update = Update(**update_data)
        await dispatcher.feed_update(bot, update)
        return {'status': 'ok'}

    except Exception as e:
        logging.error(f'Error processing Telegram update: {e}')
        raise HTTPException(status_code=500, detail='Internal Server Error')


@telegram_webhook_router.get(path='/webhook/health', response_model=Dict[str, str])
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint to verify the webhook is operational.
    
    :return: Dict[str, str] - Health status message.
    """
    return {'status': 'healthy', 'message': 'Webhook is operational. Bye, have a great time!'}
