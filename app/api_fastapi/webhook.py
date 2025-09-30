import logging
from typing import Dict, Any

from aiogram.types import Update
from fastapi import APIRouter, Request, HTTPException, Header
from fastapi.responses import JSONResponse

from app.bot_telegram import BotManager
from config import settings

webhook_router = APIRouter()


class WebhookHandler:
    """
    Handler for Telegram webhook requests.
    """

    def __init__(self):
        self.bot_manager = BotManager()
        self.bot = self.bot_manager.create_bot()
        self.dispatcher = self.bot_manager.create_dispatcher()
        self.webhook_secret = settings.telegram.webhook_secret

    def _verify_webhook_secret(self, secret_header: str) -> bool:
        """
        Verify the webhook secret token.

        :param secret_header: The value of the 'X-Telegram-Bot-Api-Secret-Token' header
        :return: True if the secret is valid, False otherwise
        """
        if not self.webhook_secret or not secret_header:
            logging.error('Verifying webhook secret failed.')
            return False

        normalized_header = str(secret_header).strip()
        normalized_secret = str(self.webhook_secret).strip()

        if len(normalized_header) < 1 or len(normalized_secret) < 1:
            logging.error('Verifying webhook secret failed due to empty values.')
            return False

        return normalized_secret == normalized_header

    async def process_update(self, update_data: Dict[str, Any], secret_header: str) -> Dict[str, str]:
        """
        Process an incoming Telegram update.

        :param update_data: The update data as a dictionary
        :param secret_header: Secret token from the header
        :return: Dict[str, str] - response status
        """
        if not self._verify_webhook_secret(secret_header):
            logging.error('Invalid webhook secret token.')
            raise HTTPException(status_code=403, detail='Forbidden')

        try:
            update = Update(**update_data)

            await self.dispatcher.feed_update(self.bot, update)
            return {'status': 'ok'}

        except Exception as e:
            logging.error(f'Error processing update: {e}')
            raise HTTPException(
                status_code=500, detail='Internal Server Error')


webhook_handler = WebhookHandler()


@webhook_router.post(path='/webhook', response_model=Dict[str, str])
async def telegram_webhook(
        request: Request,
        x_telegram_bot_api_secret_token: str = Header(
            default=None, alias='X-Telegram-Bot-Api-Secret-Token')
) -> Dict[str, str]:
    try:

        update_data = await request.json()

        response = await webhook_handler.process_update(
            update_data=update_data,
            secret_header=x_telegram_bot_api_secret_token
        )

        return response

    except Exception as e:
        logging.error(f'Unexpected error in webhook endpoint: {e}')
        return JSONResponse(
            status_code=500, 
            content={'status': 'error', 'message': 'Internal Server Error'}
            )


@webhook_router.get(path='/webhook/health', response_model=Dict[str, str])
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint for the webhook.

    :return: Dict[str, str] - response status
    """
    return {'status': 'healthy', 'message': 'Webhook is operational.'}
