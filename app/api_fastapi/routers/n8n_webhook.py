import logging
import traceback

from fastapi import APIRouter, HTTPException, Header, Depends, status

from app.api_fastapi.dependencies import (
    get_chat_service,
    get_survey_service,
    get_user_service,
    get_penalty_service,
    get_message_queue_service,
    verify_n8n_webhook_secret
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
from app.models import Chat, Survey, User
from app.services import (
    ChatService,
    SurveyService,
    UserService,
    PenaltyService,
    MessageQueueService
)
from app.utils import escape_markdown
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

        answers_set: set[str] = {
            answer.answer.lower() for answer in survey_responses.answers
        }

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
            if callsign.lower() not in answers_set
        }

        return survey, not_answered_users

    except ValueError as ve:
        logger.error('Validation error in _prepare_not_answered_users_object: %s', str(ve))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Invalid survey responses data.') from ve
    except Exception as e:
        logger.error('Unexpected error in _prepare_not_answered_users_object: %s\n%s', str(e), traceback.format_exc())
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail='Internal Server Error while preparing survey data.') from e


def _split_users_into_chunks(
        base_text: str,
        users_list: list[str],
        max_length: int = 4096
) -> list[str]:
    """
    Splits users list into multiple message chunks if combined with base_text exceeds max_length.
    Each chunk contains base_text + portion of users.
    
    Args:
        base_text: The base message text (e.g., "⚠️ Опрос не прошли:\n").
        users_list: List of username strings (e.g., ['@username1', '@username2']).
        max_length: Maximum length of each message (default: 4096).
    
    Returns:
        List of message strings. First message has base_text + users,
        subsequent messages have only users.
    """
    if not users_list:
        return [base_text]

    if len(base_text) > max_length:
        raise ValueError('Base text alone exceeds maximum message length')

    messages: list[str] = []
    current_chunk: list[str] = []
    current_length: int = len(base_text)
    is_first_message: bool = True

    for user in users_list:
        separator: str = ', ' if current_chunk else ''
        users_with_separator_length: int = len(separator) + len(user)

        if current_length + users_with_separator_length > max_length:
            if current_chunk:
                if is_first_message:
                    messages.append(base_text + ', '.join(current_chunk))
                    is_first_message = False
                else:
                    messages.append(', '.join(current_chunk))

            current_chunk: list[str] = [user]
            current_length: int = len(user)
        else:
            current_chunk.append(user)
            current_length += users_with_separator_length

    if current_chunk:
        if is_first_message:
            messages.append(base_text + ', '.join(current_chunk))
        else:
            messages.append(', '.join(current_chunk))

    return messages


@n8n_webhook_router.post(path='/webhook/new-form', response_model=WebhookResponse)
async def new_form_webhook(
        form_data: NewFormSchema,
        chat_service: ChatService = Depends(get_chat_service),
        message_queue_service: MessageQueueService = Depends(get_message_queue_service),
        _: str = Depends(verify_n8n_webhook_secret),
        _x_n8n_secret_token: str = Header(
            default=None,
            alias='X-N8N-Secret-Token'
        )
) -> WebhookResponse:
    """
    Endpoint to handle incoming new form webhook from n8n.

    Args:
        form_data (NewFormSchema): new form data.
        chat_service (ChatService): instance of ChatService.
        message_queue_service (MessageQueueService): instance of MessageQueueService.
        _ (str): Verified webhook secret token.
        _x_n8n_secret_token (str): n8n secret token from header.

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
            return WebhookResponse(
                success='ok',
                data={'message': 'No bound chat configured for sending form data.'}
            )

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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail='Internal Server Error while processing new form.') from e


@n8n_webhook_router.post(path='/webhook/send-survey-completion-status', response_model=WebhookResponse)
async def survey_completion_status_webhook(
        survey_responses: SurveyResponseSchema,
        chat_service: ChatService = Depends(get_chat_service),
        survey_service: SurveyService = Depends(get_survey_service),
        user_service: UserService = Depends(get_user_service),
        _: str = Depends(verify_n8n_webhook_secret),
        _x_n8n_secret_token: str = Header(
            default=None,
            alias='X-N8N-Secret-Token'
        )
) -> WebhookResponse:
    """
    Endpoint to handle incoming survey completion status webhook from n8n.

    Args:
        survey_responses (SurveyResponseSchema): survey responses data.
        chat_service (ChatService): instance of ChatService.
        survey_service (SurveyService): instance of SurveyService.
        user_service (UserService): instance of UserService.
        _ (str): Verified webhook secret token.
        _x_n8n_secret_token (str): n8n secret token from header.

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
            return WebhookResponse(
                success='ok',
                data={'message': 'No bound chat configured for sending survey completion status.'}
            )

        survey, not_answered_users = await _prepare_not_answered_users_object(
            survey_service=survey_service,
            user_service=user_service,
            survey_responses=survey_responses
        )

        if not_answered_users:
            not_answered_list_items: list[str] = [
                f'@{escape_markdown(data.username)}' if data.username
                else callsign
                for callsign, data in not_answered_users.items()
            ]

            base_not_answered_text: str = (
                f'⚠️ Опрос по мероприятию [{survey.title}]({survey.form_url}) '
                f'не прошли:\n'
            )

            not_answered_messages: list[str] = _split_users_into_chunks(
                base_text=base_not_answered_text,
                users_list=not_answered_list_items,
                max_length=4096
            )

            reminder_text: str = (
                f'🔔 Напоминаю, что опрос нужно пройти до\n\n'
                f'*{survey.ended_at.astimezone(tz=settings.timezone_zoneinfo).strftime("%d.%m.%Y %H:%M")}*\n\n'
                f'Если опрос не будет пройден до указанной даты, вы получите штрафной балл.\n'
                f'Три штрафных балла приведут к автоматическому исключению из команды.\n\n'
                f'🔗 [Перейти к опросу]({survey.form_url})'
            )

            messages_to_send: list[TelegramMessage] = []

            for msg_text in not_answered_messages:
                messages_to_send.append(
                    TelegramMessage(
                        chat_id=bound_chat.telegram_id,
                        message_thread_id=bound_thread_id,
                        text=msg_text,
                        disable_web_page_preview=True,
                        parse_mode='Markdown'
                    )
                )

            messages_to_send.append(
                TelegramMessage(
                    chat_id=bound_chat.telegram_id,
                    message_thread_id=bound_thread_id,
                    text=reminder_text,
                    parse_mode='Markdown'
                )
            )

            send_bulk_messages.delay([msg.model_dump() for msg in messages_to_send])

        return WebhookResponse(success='received', data=survey_responses.model_dump())

    except HTTPException:
        raise
    except Exception as e:
        logger.error('Error processing survey completion status: %s\n%s', str(e), traceback.format_exc())
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail='Internal Server Error while processing survey completion status.') from e


@n8n_webhook_router.post(path='/webhook/send-survey-finished', response_model=WebhookResponse)
async def send_survey_finished_webhook(
        survey_responses: SurveyResponseSchema,
        chat_service: ChatService = Depends(get_chat_service),
        survey_service: SurveyService = Depends(get_survey_service),
        user_service: UserService = Depends(get_user_service),
        penalty_service: PenaltyService = Depends(get_penalty_service),
        message_queue_service: MessageQueueService = Depends(get_message_queue_service),
        _: str = Depends(verify_n8n_webhook_secret),
        _x_n8n_secret_token: str = Header(
            default=None,
            alias='X-N8N-Secret-Token'
        )
) -> WebhookResponse:
    """
    Endpoint to handle incoming survey finished webhook from n8n.
    Also handles penalizing users who did not complete the survey and banning users with 3 penalties.

    Args:
        survey_responses (SurveyResponseSchema): survey responses data.
        chat_service (ChatService): instance of ChatService.
        survey_service (SurveyService): instance of SurveyService.
        user_service (UserService): instance of UserService.
        penalty_service (PenaltyService): instance of PenaltyService.
        message_queue_service (MessageQueueService): instance of MessageQueueService.
        _ (str): Verified webhook secret token.
        _x_n8n_secret_token (str): n8n secret token from header.

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
            return WebhookResponse(
                success='ok',
                data={'message': 'No bound chat configured for sending survey finished message.'}
            )

        survey, not_answered_users = await _prepare_not_answered_users_object(
            survey_service=survey_service,
            user_service=user_service,
            survey_responses=survey_responses
        )

        all_messages_to_send: list[TelegramMessage] = []

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
                        f'@{escape_markdown(data.username)}' if data.username
                        else callsign
                    )

            base_penalized_users_text: str = (
                f'⚠️ Опрос по мероприятию [{survey.title}]({survey.form_url}) завершен.\n\n'
                f'Ниже перечислены пользователи, которые не прошли опрос вовремя '
                f'и получили +1 штрафной балл\n\n(3 штрафных балла = исключение из команды):\n'
            )

            penalized_messages: list[str] = _split_users_into_chunks(
                base_text=base_penalized_users_text,
                users_list=penalized_users_list,
                max_length=4096
            )

            for msg_text in penalized_messages:
                all_messages_to_send.append(
                    TelegramMessage(
                        chat_id=bound_chat.telegram_id,
                        message_thread_id=bound_thread_id,
                        text=msg_text,
                        disable_web_page_preview=True,
                        parse_mode='Markdown'
                    )
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

            banned_users_list: list[str] = [
                f'@{user_data.username}'.replace('_', r'\_')
                if user_data.username else user_data.callsign
                for user_data in users_with_three_penalties
            ]

            base_banned_text: str = (
                f'🚫 Пользователи, достигшие 3 штрафных баллов, '
                f'были автоматически исключены из команды:\n'
            )

            banned_messages: list[str] = _split_users_into_chunks(
                base_text=base_banned_text,
                users_list=banned_users_list,
                max_length=4096
            )

            for msg_text in banned_messages:
                all_messages_to_send.append(
                    TelegramMessage(
                        chat_id=bound_chat.telegram_id,
                        message_thread_id=bound_thread_id,
                        text=msg_text,
                        parse_mode='Markdown'
                    )
                )

        if all_messages_to_send:
            send_bulk_messages.delay([msg.model_dump() for msg in all_messages_to_send])

        return WebhookResponse(
            success='received',
            data=survey_responses.model_dump(),
            users_with_three_penalties=users_with_three_penalties
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error('Error processing survey finished data: %s\n%s', str(e), traceback.format_exc())
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail='Internal Server Error while processing survey finished data.') from e
