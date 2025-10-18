import logging
import traceback

from fastapi import APIRouter, HTTPException, Header, Depends, Request

from app.api_fastapi.dependencies import (
    get_chat_service,
    get_survey_service,
    get_user_service,
    get_penalty_service,
    get_message_queue_service,
)
from app.api_fastapi.schemas import (
    NewFormSchema,
    SurveyResponseSchema,
    UserInfo,
    UserPenaltyInfo,
    TelegramMessage,
    WebhookResponse
)
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

logger = logging.getLogger(__name__)
n8n_webhook_router: APIRouter = APIRouter()


async def _prepare_not_answered_users_object(
        survey_service: SurveyService,
        user_service: UserService,
        survey_responses: SurveyResponseSchema
) -> tuple[Survey, dict[str, UserInfo]]:
    """
    Prepares the survey and a dictionary of users who did not answer the survey.

    Args:
        survey_service (SurveyService): Instance of SurveyService to fetch survey details.
        user_service (UserService): Instance of UserService to fetch user details.
        survey_responses (SurveyResponseSchema): The survey responses data.

    Raises:
        HTTPException: If any error occurs during processing.

    Returns:
        A tuple containing the survey object and a dictionary
        of users who did not answer the survey. The dictionary keys are user callsigns, and
        the values are dictionaries with user details (telegram_id, username, first_name, last_name).
        If all users have answered, returns an empty dictionary.
    """
    try:
        survey: Survey = \
            await survey_service.get_survey_by_google_form_id(survey_responses.google_form_id)

        answers_list: list[str] = [
            answer.answer.lower() for answer in survey_responses.answers
        ]

        users_without_reservation: list[User] = \
            await user_service.get_users_without_reservation_exclude_creators()

        callsign_to_data: dict[str, UserInfo] = {
            user.callsign: UserInfo(
                telegram_id=user.telegram_id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            ) for user in users_without_reservation
        }

        not_answered_users: dict[str, UserInfo] = {
            callsign: data for callsign, data in callsign_to_data.items()
            if callsign.lower() not in answers_list
        }

        return survey, not_answered_users

    except ValueError as ve:
        logger.error('Validation error in _prepare_not_answered_users_object: %s', str(ve))
        raise HTTPException(status_code=400, detail='Invalid survey responses data.') from ve
    except Exception as e:
        logger.error('Unexpected error in _prepare_not_answered_users_object: %s\n%s', str(e), traceback.format_exc())
        raise HTTPException(status_code=500, detail='Internal Server Error while preparing survey data.') from e


@n8n_webhook_router.post(path='/webhook/new-form', response_model=WebhookResponse)
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
) -> WebhookResponse:
    """
    Endpoint to handle incoming new form webhook from n8n.

    Args:
        request: Request - FastAPI request object containing the new form data. (Unused but kept for decorator consistency)
        form_data: NewFormSchema - new form data.
        x_n8n_secret_token: str - n8n secret token from header. (Unused but kept for testing via docs)
        chat_service: ChatService - instance of ChatService.
        message_queue_service: MessageQueueService - instance of MessageQueueService.

    Raises:
        HTTPException: If no bound chat is found or if any other error occurs during processing.

    Returns:
        Acknowledgment of successful processing of the new form.
    """
    try:
        bound_chat: Chat | None = await chat_service.get_bound_chat()
        bound_thread_id: int | None = bound_chat.thread_id if bound_chat else None

        if not bound_chat:
            logger.warning('No bound chat found to send the form data.')
            raise HTTPException(status_code=400, detail='No bound chat configured for sending form notifications.')

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

        return WebhookResponse(success='received', data=form_data.model_dump())

    except HTTPException:
        raise
    except Exception as e:
        logger.error('Error processing new form webhook: %s\n%s', str(e), traceback.format_exc())
        raise HTTPException(
            status_code=500, detail='Internal Server Error while processing new form.'
        ) from e


@n8n_webhook_router.post(path='/webhook/send-survey-completion-status', response_model=WebhookResponse)
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
) -> WebhookResponse:
    """
    Endpoint to handle incoming survey completion status webhook from n8n.

    Args:
        request: Request - FastAPI request object containing the survey responses data. (Unused but kept for decorator consistency)
        survey_responses: SurveyResponseSchema - survey responses data.
        x_n8n_secret_token: str - n8n secret token from header. (Unused but kept for testing via docs)
        chat_service: ChatService - instance of ChatService.
        survey_service: SurveyService - instance of SurveyService.
        user_service: UserService - instance of UserService.

    Raises:
        HTTPException: If no bound chat is found or if any other error occurs during processing.

    Returns:
        Acknowledgment of successful processing along with survey responses.
    """
    try:
        bound_chat: Chat | None = await chat_service.get_bound_chat()
        bound_thread_id: int | None = bound_chat.thread_id if bound_chat else None

        if not bound_chat:
            logger.warning('No bound chat found to send the survey completion status.')
            raise HTTPException(status_code=400,
                                detail='No bound chat configured for sending survey completion status.')

        survey, not_answered_users = await _prepare_not_answered_users_object(
            survey_service=survey_service,
            user_service=user_service,
            survey_responses=survey_responses
        )

        if not_answered_users:
            not_answered_list: str = ', '.join(
                f'@{data.username}'.replace('_', r'\_') if data.username
                else callsign
                for callsign, data in not_answered_users.items()
            )

            not_answered_text: str = (
                f'⚠️ Опрос по мероприятию [{survey.title}]({survey.form_url}) '
                f'не прошли:\n{not_answered_list}'
            )

            reminder_text: str = (
                f'🔔 Напоминаю, что опрос нужно пройти до\n\n'
                f'*{survey.ended_at.astimezone(tz=settings.timezone_zoneinfo).strftime("%d.%m.%Y %H:%M")}*\n\n'
                f'Если опрос не будет пройден до указанной даты, вы получите штрафной балл.\n'
                f'Три штрафных балла приведут к автоматическому исключению из команды.\n\n'
                f'🔗 [Перейти к опросу]({survey.form_url})'
            )

            messages_to_send: list[TelegramMessage] = [
                TelegramMessage(
                    chat_id=bound_chat.telegram_id,
                    message_thread_id=bound_thread_id,
                    text=not_answered_text,
                    disable_web_page_preview=True,
                    parse_mode='Markdown'
                ),
                TelegramMessage(
                    chat_id=bound_chat.telegram_id,
                    message_thread_id=bound_thread_id,
                    text=reminder_text,
                    parse_mode='Markdown'
                )
            ]

            send_bulk_messages.delay([msg.model_dump() for msg in messages_to_send])

        return WebhookResponse(success='received', data=survey_responses.model_dump())

    except HTTPException:
        raise
    except Exception as e:
        logger.error('Error processing survey completion status: %s\n%s', str(e), traceback.format_exc())
        raise HTTPException(
            status_code=500, detail='Internal Server Error while processing survey completion status.'
        ) from e


@n8n_webhook_router.post(path='/webhook/send-survey-finished', response_model=WebhookResponse)
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
) -> WebhookResponse:
    """
    Endpoint to handle incoming survey finished webhook from n8n.
    Also handles penalizing users who did not complete the survey and banning users with 3 penalties.

    Args:
        request: Request - FastAPI request object containing the survey responses data. (Unused but kept for decorator consistency)
        survey_responses: SurveyResponseSchema - survey responses data.
        x_n8n_secret_token: str - n8n secret token from header. (Unused but kept for testing via docs)
        chat_service: ChatService - instance of ChatService.
        survey_service: SurveyService - instance of SurveyService.
        user_service: UserService - instance of UserService.
        penalty_service: PenaltyService - instance of PenaltyService.
        message_queue_service: MessageQueueService - instance of MessageQueueService.

    Raises:
        HTTPException: If no bound chat is found or if any other error occurs during processing.

    Returns:
        Acknowledgment of successful processing along with survey responses and users with three penalties.
    """
    try:
        bound_chat: Chat | None = await chat_service.get_bound_chat()
        bound_thread_id: int | None = bound_chat.thread_id if bound_chat else None

        if not bound_chat:
            logger.warning('No bound chat found to send the survey finished message.')
            raise HTTPException(status_code=400, detail='No bound chat configured for sending survey finished message.')

        survey, not_answered_users = await _prepare_not_answered_users_object(
            survey_service=survey_service,
            user_service=user_service,
            survey_responses=survey_responses
        )

        if not_answered_users:
            penalized_users_list: list[str] = []
            for callsign, data in not_answered_users.items():
                user: User | None = \
                    await user_service.get_active_user_by_callsign_exclude_creator(callsign)
                if user:
                    await penalty_service.add_penalty(
                        user_id=user.id,
                        survey_id=survey.id,
                        reason=f'Не прошёл опрос по мероприятию "{survey.title}"'
                    )
                penalized_users_list.append(
                    f'@{data.username}'.replace('_', r'\_') if data.username
                    else callsign
                )

            penalized_users_text: str = (
                f'⚠️ Опрос по мероприятию [{survey.title}]({survey.form_url}) завершен.\n\n'
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

        users_with_three_penalties_raw: list[dict[str, str | int]] = \
            await penalty_service.get_all_users_with_three_penalties()

        users_with_three_penalties: list[UserPenaltyInfo] = [
            UserPenaltyInfo(**user_data)
            for user_data in users_with_three_penalties_raw
        ]

        if users_with_three_penalties:
            for user_data in users_with_three_penalties:
                ban_user_from_chat.delay(bound_chat.telegram_id, user_data.telegram_id)
                await user_service.deactivate_user(user_data.telegram_id)

            callsigns: str = ', '.join(
                f'@{user_data.username}'.replace('_', r'\_')
                if user_data.username else user_data.callsign
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

        return WebhookResponse(
            success='received',
            data=survey_responses.model_dump(),
            users_with_three_penalties=users_with_three_penalties
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error('Error processing survey finished data: %s\n%s', str(e), traceback.format_exc())
        raise HTTPException(
            status_code=500, detail='Internal Server Error while processing survey finished data.'
        ) from e
