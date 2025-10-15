from aiogram import Bot, Dispatcher

from app.bot_telegram import BotManager
from app.services import (
    MessageQueueService,
    ChatService,
    SurveyService,
    UserService,
    PenaltyService
)

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
