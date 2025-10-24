import logging
from typing import Annotated

from aiogram import Bot, Dispatcher
from fastapi import Header, HTTPException, status

from app.bot_telegram import BotManager
from app.services import (
    MessageQueueService,
    ChatService,
    SurveyService,
    UserService,
    PenaltyService
)
from config import settings

logger = logging.getLogger(__name__)

_bot_manager: BotManager = BotManager()
_bot: Bot = _bot_manager.create_bot()
_dispatcher: Dispatcher = _bot_manager.create_dispatcher()


def get_bot_manager() -> BotManager:
    """
    Dependency to get an instance of BotManager.

    Returns:
        Instance of BotManager.
    """
    return _bot_manager


def get_bot() -> Bot:
    """
    Dependency to get an instance of Bot.

    Returns:
        Instance of Bot.
    """
    return _bot


def get_dispatcher() -> Dispatcher:
    """
    Dependency to get an instance of Dispatcher.

    Returns:
        Instance of Dispatcher.
    """
    return _dispatcher


def get_chat_service() -> ChatService:
    """
    Dependency to get an instance of ChatService.

    Returns:
        Instance of ChatService.
    """
    return ChatService()


def get_survey_service() -> SurveyService:
    """
    Dependency to get an instance of SurveyService.

    Returns:
        Instance of SurveyService.
    """
    return SurveyService()


def get_user_service() -> UserService:
    """
    Dependency to get an instance of UserService.

    Returns:
        Instance of UserService.
    """
    return UserService()


def get_message_queue_service() -> MessageQueueService:
    """
    Dependency to get an instance of MessageQueueService.

    Returns:
        Instance of MessageQueueService.
    """
    return MessageQueueService()


def get_penalty_service() -> PenaltyService:
    """
    Dependency to get an instance of PenaltyService.

    Returns:
        Instance of PenaltyService.
    """
    return PenaltyService()


async def verify_telegram_webhook_secret(
        x_telegram_bot_api_secret_token: Annotated[
            str | None,
            Header(alias='X-Telegram-Bot-Api-Secret-Token')
        ] = None
) -> str:
    """
    Dependency to verify the Telegram webhook secret token.
    
    Args:
        x_telegram_bot_api_secret_token: The secret token from the request header.
    
    Raises:
        HTTPException: If the secret token is missing or invalid.
    Returns:
        The validated secret token.
    """
    expected_secret: str | None = settings.telegram.webhook_secret

    if not expected_secret:
        logger.error('Webhook secret is not configured in settings.')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Server configuration error.'
        )

    if not x_telegram_bot_api_secret_token:
        logger.warning('Missing X-Telegram-Bot-Api-Secret-Token header in request.')
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Unauthorized.'
        )

    normalized_header: str = str(x_telegram_bot_api_secret_token).strip()
    normalized_secret: str = str(expected_secret).strip()

    if not normalized_header or len(normalized_header) < 1:
        logger.warning('Empty X-Telegram-Bot-Api-Secret-Token header in request.')
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Unauthorized.'
        )

    if normalized_header != normalized_secret:
        logger.warning('Invalid X-Telegram-Bot-Api-Secret-Token header in request.')
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Unauthorized.'
        )

    return normalized_header


async def verify_n8n_webhook_secret(
        x_n8n_secret_token: Annotated[
            str | None,
            Header(alias='X-N8N-Secret-Token')
        ] = None
) -> str:
    """
    Dependency to verify the N8N webhook secret token.
    
    Args:
        x_n8n_secret_token: The secret token from the request header.

    Raises:
        HTTPException: If the token is invalid or missing.

    Returns:
        The validated secret token.
    """
    from config import settings

    expected_secret: str | None = settings.n8n.n8n_webhook_secret

    if not expected_secret:
        logger.error('N8N webhook secret not configured in settings.')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Server configuration error.'
        )

    if not x_n8n_secret_token:
        logger.warning('Missing X-N8N-Secret-Token header.')
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Unauthorized.'
        )

    normalized_header: str = x_n8n_secret_token.strip()
    normalized_secret: str = expected_secret.strip()

    if not normalized_header or len(normalized_header) < 1:
        logger.warning('Empty X-N8N-Secret-Token header.')
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Unauthorized.'
        )

    if normalized_secret != normalized_header:
        logger.warning('Invalid X-N8N-Secret-Token header.')
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Unauthorized.'
        )

    return normalized_header
