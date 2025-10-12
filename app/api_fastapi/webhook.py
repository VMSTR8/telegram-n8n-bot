import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple

from aiogram import Bot, Dispatcher
from aiogram.types import Update
from fastapi import APIRouter, Request, HTTPException, Header

from app.api_fastapi.schemas import NewFormSchema, SurveyResponseSchema
from app.bot_telegram import BotManager
from app.models import Chat, Survey
from app.services import (
    MessageQueueService,
    ChatService,
    SurveyService,
    UserService
)
from config import settings

telegram_webhook_router = APIRouter()


class WebhookHandler:
    """
    Handler for Telegram webhook requests.
    """

    def __init__(self):
        self.bot_manager: BotManager = BotManager()
        self.bot: Bot = self.bot_manager.create_bot()
        self.dispatcher: Dispatcher = self.bot_manager.create_dispatcher()
        self.chat_service: ChatService = ChatService()
        self.survey_service: SurveyService = SurveyService()
        self.user_service: UserService = UserService()
        self.message_service: MessageQueueService = MessageQueueService()
        self.webhook_secret: Optional[str] = settings.telegram.webhook_secret
        self.n8n_secret: Optional[str] = settings.n8n.n8n_webhook_secret

    def _verify_telegram_api_webhook_secret(self, secret_header: str) -> bool:
        """
        Verify the webhook secret token.

        :param secret_header: The value of the 'X-Telegram-Bot-Api-Secret-Token' header
        :return: True if the secret is valid, False otherwise
        """
        if not self.webhook_secret or not secret_header:
            logging.error('Verifying webhook secret failed.')
            return False

        normalized_header: str = str(secret_header).strip()
        normalized_secret: str = str(self.webhook_secret).strip()

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
        if not self.n8n_secret or not secret_header:
            logging.error('Verifying n8n webhook signature failed.')
            return False

        normalized_signature: str = str(secret_header).strip()
        normalized_secret: str = str(self.n8n_secret).strip()

        if len(normalized_signature) < 1 or len(normalized_secret) < 1:
            return False

        return normalized_secret == normalized_signature

    async def _prepare_not_answered_users_object(
            self,
            survey_responses: SurveyResponseSchema
    ) -> Optional[Tuple[Survey, Dict[str, Dict[str, Any]]]]:
        """
        Prepare the object containing users who have not completed the survey.
        
        :param survey_responses: The survey responses data
        :return: Tuple containing the survey and a dictionary of users who have not completed the survey
        """
        survey: Survey = \
            await self.survey_service.get_survey_by_google_form_id(survey_responses.google_form_id)

        answers_list: List[str] = [
            answer.answer.lower() for answer in survey_responses.answers
        ]

        users_without_reservation = await self.user_service.get_users_without_reservation()

        callsign_to_data: Dict[str, Dict[str, Any]] = {
            user.callsign: {
                'telegram_id': user.telegram_id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name
            } for user in users_without_reservation
        }

        not_answered_users: Dict[str, Dict[str, Any]] = {
            callsign: data for callsign, data in callsign_to_data.items()
            if callsign.lower() not in answers_list
        }

        return survey, not_answered_users

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
            update: Update = Update(**update_data)

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
            bound_chat: Optional[Chat] = await self.chat_service.get_bound_chat()
            bound_thread_id: Optional[int] = bound_chat.thread_id if bound_chat else None

            if not bound_chat:
                logging.error('No bound chat found to send the form data.')
                raise HTTPException(status_code=400, detail='No bound chat found.')

            new_form_text: str = (
                f'Запущен новый опрос:\n\n'
                f'• *{form_data.title}*\n'
                f'🕒 Пройти до: {form_data.ended_at.astimezone(tz=settings.timezone_zoneinfo
                                                              ).strftime("%d.%m.%Y %H:%M")}\n'
                f'🔗 [Перейти к опросу]({form_data.form_url})\n'
            )

            await self.message_service.send_and_pin_message(
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

    async def process_survey_completion_status_received(
            self,
            survey_responses: SurveyResponseSchema,
            secret_header: str
    ) -> Dict[str, Any]:
        """
        Process survey completion status received from n8n.

        :param survey_responses: The survey responses data
        :param secret_header: Signature from the header
        :return: Dict[str, Any] - response status and data
        """
        if not self._verify_n8n_secret(secret_header):
            logging.error('Invalid n8n webhook signature.')
            raise HTTPException(status_code=403, detail='Forbidden')

        try:
            bound_chat: Optional[Chat] = await self.chat_service.get_bound_chat()
            bound_thread_id: Optional[int] = bound_chat.thread_id if bound_chat else None

            if not bound_chat:
                logging.error('No bound chat found to send the survey completion status.')
                raise HTTPException(status_code=400, detail='No bound chat found.')

            survey, not_answered_users = await self._prepare_not_answered_users_object(
                survey_responses=survey_responses
            )

            if not_answered_users:
                not_answered_list: str = ', '.join(
                    f'@{data['username']}'.replace('_', r'\_') if data.get('username')
                    else callsign
                    for callsign, data in not_answered_users.items()
                )

                escaped_title = survey.title.replace('_', r'\_')
                not_answered_text: str = (
                    f'Опрос по мероприятию [{escaped_title}]({survey.form_url}) '
                    f'не прошли:\n{not_answered_list}'
                )

                reminder_text: str = (
                    f'Напоминаю, что опрос нужно пройти до\n\n'
                    f'*{survey.ended_at.astimezone(tz=settings.timezone_zoneinfo).strftime("%d.%m.%Y %H:%M")}*\n\n'
                    f'Если опрос не будет пройден до указанной даты, вы получите штрафной балл.\n'
                    f'Три штрафных балла приведут к автоматическому исключению из команды.\n\n'
                    f'🔗 [Перейти к опросу]({survey.form_url})'
                )

                await self.message_service.send_message(
                    chat_id=bound_chat.telegram_id,
                    message_thread_id=bound_thread_id,
                    text=not_answered_text,
                    disable_web_page_preview=True,
                    parse_mode='Markdown'
                )

                await asyncio.sleep(1)

                await self.message_service.send_message(
                    chat_id=bound_chat.telegram_id,
                    message_thread_id=bound_thread_id,
                    text=reminder_text,
                    parse_mode='Markdown'
                )

            return {'status': 'received', 'data': survey_responses}

        except Exception as e:
            logging.error(f'Error processing survey completion status: {e}')
            raise HTTPException(
                status_code=500, detail='Internal Server Error'
            )

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
    update_data: Dict[str, Any] = await request.json()

    response: Dict[str, str] = await telegram_webhook_handler.process_telegram_api_update(
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
    response: Dict[str, Any] = await telegram_webhook_handler.process_new_form_data_received(
        form_data=form_data,
        secret_header=x_n8n_secret_token
    )

    return response


@telegram_webhook_router.post(path='/webhook/send-survey-completion-status', response_model=Dict[str, Any])
async def survey_completion_status_webhook(
        survey_responses: SurveyResponseSchema,
        x_n8n_secret_token: str = Header(
            default=None,
            alias='X-N8N-Secret-Token'
        )
) -> Dict[str, Any]:
    """
    Webhook endpoint to receive survey completion status from n8n.

    :param survey_responses: SurveyResponseSchema - the survey responses data
    :param x_n8n_secret_token: str - signature header for verification
    :return: Dict[str, Any] - response status and data
    """
    response: Dict[str, Any] = await telegram_webhook_handler.process_survey_completion_status_received(
        survey_responses=survey_responses,
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
