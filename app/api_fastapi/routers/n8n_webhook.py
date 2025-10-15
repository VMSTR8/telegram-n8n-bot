import logging
from typing import Dict, Any, Optional, List, Tuple

from fastapi import APIRouter, HTTPException, Header, Depends, Request

from app.api_fastapi.dependencies import (
    get_chat_service,
    get_survey_service,
    get_user_service,
    get_penalty_service,
    get_message_queue_service,
)
from app.api_fastapi.schemas import NewFormSchema, SurveyResponseSchema
from app.celery_tasks import ban_user_from_chat, send_bulk_messages
from app.decorators import FastAPIValidate
from app.models import Chat, Survey, User
from app.services import (
    ChatService,
    SurveyService,
    UserService,
    PenaltyService,
    MessageQueueService
)
from config import settings

n8n_webhook_router = APIRouter()


async def _prepare_not_answered_users_object(
        survey_service,
        user_service,
        survey_responses: SurveyResponseSchema
) -> Optional[Tuple[Survey, Dict[str, Dict[str, Any]]]]:
    """
    Prepares the survey and not answered users object.

    :param survey_service: SurveyService - instance of SurveyService.
    :param user_service: UserService - instance of UserService.
    :param survey_responses: SurveyResponseSchema - survey responses data.
    :return: Optional[Tuple[Survey, Dict[str, Dict[str, Any]]]] - survey and not answered users data.
    """
    survey: Survey = \
        await survey_service.get_survey_by_google_form_id(survey_responses.google_form_id)

    answers_list: List[str] = [
        answer.answer.lower() for answer in survey_responses.answers
    ]

    users_without_reservation: List[User] = await user_service.get_users_without_reservation()

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


@n8n_webhook_router.post(path='/webhook/new-form', response_model=Dict[str, Any])
@FastAPIValidate.validate_header_secret(
    header_name='X-N8N-Secret-Token',
    secret=settings.n8n.n8n_webhook_secret
)
async def new_form_webhook(
        request: Request,
        form_data: NewFormSchema,
        x_n8n_secret_token: str = Header(
            default=None,
            alias='X-N8N-Secret-Token'
        ),
        chat_service: ChatService = Depends(get_chat_service),
        message_queue_service: MessageQueueService = Depends(get_message_queue_service)
) -> Dict[str, Any]:
    """
    Endpoint to handle incoming new form webhook from n8n.

    :param request: Request - FastAPI request object containing the form data. (Unused but kept for decorator consistency)
    :param form_data: NewFormSchema - new form data.
    :param x_n8n_secret_token: str - n8n secret token from header. (Unused but kept for testing via docs)
    :param chat_service: ChatService - instance of ChatService.
    :param message_queue_service: MessageQueueService - instance of MessageQueueService.
    :return: Dict[str, Any] - Acknowledgment of successful processing.
    """
    try:
        bound_chat: Optional[Chat] = await chat_service.get_bound_chat()
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

        await message_queue_service.send_and_pin_message(
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


@n8n_webhook_router.post(path='/webhook/send-survey-completion-status', response_model=Dict[str, Any])
@FastAPIValidate.validate_header_secret(
    header_name='X-N8N-Secret-Token',
    secret=settings.n8n.n8n_webhook_secret
)
async def survey_completion_status_webhook(
        request: Request,
        survey_responses: SurveyResponseSchema,
        x_n8n_secret_token: str = Header(
            default=None,
            alias='X-N8N-Secret-Token'
        ),
        chat_service: ChatService = Depends(get_chat_service),
        survey_service: SurveyService = Depends(get_survey_service),
        user_service: UserService = Depends(get_user_service),
) -> Dict[str, Any]:
    """
    Endpoint to handle incoming survey completion status webhook from n8n.

    :param request: Request - FastAPI request object containing the survey responses data. (Unused but kept for decorator consistency)
    :param survey_responses: SurveyResponseSchema - survey responses data.
    :param x_n8n_secret_token: str - n8n secret token from header. (Unused but kept for testing via docs)
    :param chat_service: ChatService - instance of ChatService.
    :param survey_service: SurveyService - instance of SurveyService.
    :param user_service: UserService - instance of UserService.
    :return: Dict[str, Any] - Acknowledgment of successful processing.
    """
    try:
        bound_chat: Optional[Chat] = await chat_service.get_bound_chat()
        bound_thread_id: Optional[int] = bound_chat.thread_id if bound_chat else None

        if not bound_chat:
            logging.error('No bound chat found to send the survey completion status.')
            raise HTTPException(status_code=400, detail='No bound chat found.')

        survey, not_answered_users = await _prepare_not_answered_users_object(
            survey_service=survey_service,
            user_service=user_service,
            survey_responses=survey_responses
        )

        if not_answered_users:
            not_answered_list: str = ', '.join(
                f'@{data["username"]}'.replace('_', r'\_') if data.get('username')
                else callsign
                for callsign, data in not_answered_users.items()
            )

            escaped_title: str = survey.title.replace('_', r'\_')
            not_answered_text: str = (
                f'⚠️ Опрос по мероприятию [{escaped_title}]({survey.form_url}) '
                f'не прошли:\n{not_answered_list}'
            )

            reminder_text: str = (
                f'🔔 Напоминаю, что опрос нужно пройти до\n\n'
                f'*{survey.ended_at.astimezone(tz=settings.timezone_zoneinfo).strftime("%d.%m.%Y %H:%M")}*\n\n'
                f'Если опрос не будет пройден до указанной даты, вы получите штрафной балл.\n'
                f'Три штрафных балла приведут к автоматическому исключению из команды.\n\n'
                f'🔗 [Перейти к опросу]({survey.form_url})'
            )

            messages_to_send: List[Dict[str, Any]] = [
                {
                    'chat_id': bound_chat.telegram_id,
                    'message_thread_id': bound_thread_id,
                    'text': not_answered_text,
                    'disable_web_page_preview': True,
                    'parse_mode': 'Markdown'
                },
                {
                    'chat_id': bound_chat.telegram_id,
                    'message_thread_id': bound_thread_id,
                    'text': reminder_text,
                    'parse_mode': 'Markdown'
                }
            ]

            send_bulk_messages.delay(messages_to_send)

        return {'status': 'received', 'data': survey_responses}

    except Exception as e:
        logging.error(f'Error processing survey completion status: {e}')
        raise HTTPException(
            status_code=500, detail='Internal Server Error'
        )


@n8n_webhook_router.post(path='/webhook/send-survey-finished', response_model=Dict[str, Any])
@FastAPIValidate.validate_header_secret(
    header_name='X-N8N-Secret-Token',
    secret=settings.n8n.n8n_webhook_secret
)
async def send_survey_finished_webhook(
        request: Request,
        survey_responses: SurveyResponseSchema,
        x_n8n_secret_token: str = Header(
            default=None,
            alias='X-N8N-Secret-Token'
        ),
        chat_service: ChatService = Depends(get_chat_service),
        survey_service: SurveyService = Depends(get_survey_service),
        user_service: UserService = Depends(get_user_service),
        penalty_service: PenaltyService = Depends(get_penalty_service),
        message_queue_service: MessageQueueService = Depends(get_message_queue_service)
) -> Dict[str, Any]:
    """
    Endpoint to handle incoming survey finished webhook from n8n.
    Also handles penalizing users who did not complete the survey and banning users with 3 penalties.

    :param request: Request - FastAPI request object containing the survey responses data. (Unused but kept for decorator consistency)
    :param survey_responses: SurveyResponseSchema - survey responses data.
    :param x_n8n_secret_token: str - n8n secret token from header. (Unused but kept for testing via docs)
    :param chat_service: ChatService - instance of ChatService.
    :param survey_service: SurveyService - instance of SurveyService.
    :param user_service: UserService - instance of UserService.
    :param penalty_service: PenaltyService - instance of PenaltyService.
    :param message_queue_service: MessageQueueService - instance of MessageQueueService.
    :return: Dict[str, Any] - Acknowledgment of successful processing along with survey responses and users with three penalties.
    """
    try:
        bound_chat: Optional[Chat] = await chat_service.get_bound_chat()
        bound_thread_id: Optional[int] = bound_chat.thread_id if bound_chat else None

        if not bound_chat:
            logging.error('No bound chat found to send the survey finished message.')
            raise HTTPException(status_code=400, detail='No bound chat found.')

        survey, not_answered_users = await _prepare_not_answered_users_object(
            survey_service=survey_service,
            user_service=user_service,
            survey_responses=survey_responses
        )

        if not_answered_users:
            penalized_users_list: list[str] = []
            for callsign, data in not_answered_users.items():
                user: Optional[User] = await user_service.get_active_not_creator_user_by_callsign(callsign)
                if user:
                    await penalty_service.add_penalty(
                        user_id=user.id,
                        survey_id=survey.id,
                        reason=f'Не прошёл опрос по мероприятию "{survey.title}"'
                    )
                penalized_users_list.append(
                    f'@{data["username"]}'.replace('_', r'\_') if data.get('username')
                    else callsign
                )

            escaped_title: str = survey.title.replace('_', r'\_')
            penalized_users_text: str = (
                f'⚠️ Опрос по мероприятию [{escaped_title}]({survey.form_url}) завершен.\n\n'
                f'Ниже перечислены пользователи, которые не прошли опрос вовремя '
                f'и получили +1 штрафной балл\n\n(3 штрафных балла = исключение из команды):\n'
                f'{', '.join(penalized_users_list)}'
            )

            await message_queue_service.send_message(
                chat_id=bound_chat.telegram_id,
                message_thread_id=bound_thread_id,
                text=penalized_users_text,
                disable_web_page_preview=True,
                parse_mode='Markdown'
            )

        else:
            await message_queue_service.send_message(
                chat_id=bound_chat.telegram_id,
                message_thread_id=bound_thread_id,
                text=(
                    f'✅ Опрос по мероприятию [{survey.title}]({survey.form_url}) завершен.\n\n'
                    f'Все члены команды прошли опрос вовремя!'
                ),
                parse_mode='Markdown'
            )

        users_with_three_penalties: List[Dict[str, Any]] = await penalty_service.get_all_users_with_three_penalties()

        if users_with_three_penalties:
            for user_data in users_with_three_penalties:
                ban_user_from_chat.delay(bound_chat.telegram_id, user_data['telegram_id'])

            callsigns: str = ', '.join(
                f'@{user_data['username']}'.replace('_', r'\_')
                if user_data.get('username') else user_data['callsign']
                for user_data in users_with_three_penalties
            )

            await message_queue_service.send_message(
                chat_id=bound_chat.telegram_id,
                message_thread_id=bound_thread_id,
                text=(
                    f'🚫 Пользователи, достигшие 3 штрафных баллов, были автоматически исключены из команды:\n'
                    f'{callsigns}'
                ),
                parse_mode='Markdown'
            )

        return {
            'status': 'received',
            'data': survey_responses,
            'users_with_three_penalties': users_with_three_penalties
        }

    except Exception as e:
        logging.error(f'Error processing survey finished data: {e}')
        raise HTTPException(
            status_code=500, detail='Internal Server Error'
        )
