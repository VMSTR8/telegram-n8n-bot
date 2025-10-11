import logging
from typing import Dict, Any

from aiogram.types import Update
from fastapi import APIRouter, Request, HTTPException, Header

from app.api_fastapi.schemas import NewFormSchema, SurveyResponseSchema
from app.bot_telegram import BotManager
from app.services import MessageQueueService, ChatService

from config import settings

telegram_webhook_router = APIRouter()


class WebhookHandler:
    """
    Handler for Telegram webhook requests.
    """

    def __init__(self):
        self.bot_manager = BotManager()
        self.bot = self.bot_manager.create_bot()
        self.dispatcher = self.bot_manager.create_dispatcher()
        self.webhook_secret = settings.telegram.webhook_secret
        self.n8n_secret = settings.n8n.n8n_webhook_secret

    def _verify_telegram_api_webhook_secret(self, secret_header: str) -> bool:
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
            logging.error(
                'Verifying webhook secret failed due to empty values.')
            return False

        return normalized_secret == normalized_header

    def _verify_n8n_secret(self, secret_header: str) -> bool:
        """
        Verify the n8n webhook signature.

        :param secret_header: The value of the 'X-N8N-Signature' header
        :return: True if the signature is valid, False otherwise
        """
        logging.info(self.n8n_secret)
        if not self.n8n_secret or not secret_header:
            return False

        normalized_signature = str(secret_header).strip()
        normalized_secret = str(self.n8n_secret).strip()

        if len(normalized_signature) < 1 or len(normalized_secret) < 1:
            return False

        return normalized_secret == normalized_signature

    async def process_telegram_api_update(
            self,
            update_data: Dict[str, Any],
            secret_header: str
    ) -> Dict[str, str]:
        """
        Process an incoming Telegram update.

        :param update_data: The update data as a dictionary
        :param secret_header: Secret token from the header
        :return: Dict[str, str] - response status
        """
        if not self._verify_telegram_api_webhook_secret(secret_header):
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

    async def process_new_form_data_received(
            self, 
            form_data: NewFormSchema, 
            secret_header: str
    ) -> Dict[str, Any]:
        """
        Process new form data received from n8n and notify members.

        :param form_data: The new form data
        :param secret_header: Signature from the header
        :return: Dict[str, Any] - response status and data
        """
        if not self._verify_n8n_secret(secret_header):
            logging.error('Invalid n8n webhook signature.')
            raise HTTPException(status_code=403, detail='Forbidden')

        try:
            chat_service = ChatService()
            message_service = MessageQueueService()

            bound_chat = await chat_service.get_bound_chat()
            bound_thread_id = bound_chat.thread_id if bound_chat else None

            if not bound_chat:
                logging.error('No bound chat found to send the form data.')
                raise HTTPException(status_code=400, detail='No bound chat found.')

            new_form_text = (
                f'Запущен новый опрос:\n\n'
                f'• *{form_data.title}*\n'
                f'🕒 Пройти до: {form_data.ended_at.astimezone(tz=settings.timezone_zoneinfo
                                                              ).strftime("%d.%m.%Y %H:%M")}\n'
                f'🔗 [Перейти к опросу]({form_data.form_url})\n'
            )

            await message_service.send_and_pin_message(
                chat_id=bound_chat.telegram_id,
                message_thread_id=bound_thread_id,
                text=new_form_text,
                parse_mode='Markdown'
            )

            return {'status': 'received', 'data': form_data.model_dump()}

        except Exception as e:
            logging.error(f'Error processing new form data: {e}')
            raise HTTPException(
                status_code=500, detail='Internal Server Error'
            )
    
    # async def process_survey_completion_status_received(
    #         self,
    #         survey_responses: SurveyResponseSchema,
    #         secret_header: str
    # ) -> Dict[str, Any]:
    #     if not self._verify_n8n_secret(secret_header):
    #         logging.error('Invalid n8n webhook signature.')
    #         raise HTTPException(status_code=403, detail='Forbidden')
        
    #     return {'status': 'received', 'data': survey_responses}
    
    # async def process_survey_finished_received(
    #         self,
    #         survey_responses: SurveyResponseSchema,
    #         secret_header: str
    # ) -> Dict[str, Any]:
    #     if not self._verify_n8n_secret(secret_header):
    #         logging.error('Invalid n8n webhook signature.')
    #         raise HTTPException(status_code=403, detail='Forbidden')
        
    #     return {'status': 'received', 'data': survey_responses}


telegram_webhook_handler = WebhookHandler()


@telegram_webhook_router.post(path='/webhook', response_model=Dict[str, str])
async def telegram_webhook(
        request: Request,
        x_telegram_bot_api_secret_token: str = Header(
            default=None,
            alias='X-Telegram-Bot-Api-Secret-Token'
        )
) -> Dict[str, str]:
    """
    Webhook endpoint to receive updates from Telegram.

    :param request: Request object containing the update data
    :param x_telegram_bot_api_secret_token: str - secret token from the header
    :return: Dict[str, str] - response status
    """
    update_data = await request.json()

    response = await telegram_webhook_handler.process_telegram_api_update(
        update_data=update_data,
        secret_header=x_telegram_bot_api_secret_token
    )

    return response


@telegram_webhook_router.post(path='/webhook/new-form', response_model=Dict[str, Any])
async def new_form_webhook(
        form_data: NewFormSchema,
        x_n8n_secret_token: str = Header(
            default=None,
            alias='X-N8N-Secret-Token'
        )
) -> Dict[str, Any]:
    """
    Webhook endpoint to receive new form data from n8n
    and notify members about the new form.

    :param form_data: NewFormSchema - the new form data
    :param x_n8n_secret_token: str - signature header for verification
    :return: Dict[str, Any] - response status and data
    """
    response = await telegram_webhook_handler.process_new_form_data_received(
        form_data=form_data,
        secret_header=x_n8n_secret_token
    )

    return response


@telegram_webhook_router.get(path='/webhook/health', response_model=Dict[str, str])
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint for the webhook.

    :return: Dict[str, str] - response status
    """
    return {'status': 'healthy', 'message': 'Webhook is operational.'}
