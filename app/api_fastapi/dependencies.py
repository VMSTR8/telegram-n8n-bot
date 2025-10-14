from aiogram import Bot, Dispatcher

from app.bot_telegram import BotManager
from app.services import (
    MessageQueueService,
    ChatService,
    SurveyService,
    UserService,
    PenaltyService
)

_bot_manager = BotManager()
_bot = _bot_manager.create_bot()
_dispatcher = _bot_manager.create_dispatcher()


def get_bot_manager() -> BotManager:
    """
    Dependency to get an instance of BotManager.

    :return: BotManager - instance of BotManager.
    """
    return _bot_manager


def get_bot() -> Bot:
    """
    Dependency to get an instance of Bot.

    :return: Bot - instance of Bot.
    """
    return _bot


def get_dispatcher() -> Dispatcher:
    """
    Dependency to get an instance of Dispatcher.

    :return: Dispatcher - instance of Dispatcher.
    """
    return _dispatcher


def get_chat_service() -> ChatService:
    """
    Dependency to get an instance of ChatService.

    :return: ChatService - instance of ChatService.
    """
    return ChatService()


def get_survey_service() -> SurveyService:
    """
    Dependency to get an instance of SurveyService.

    :return: SurveyService - instance of SurveyService.
    """
    return SurveyService()


def get_user_service() -> UserService:
    """
    Dependency to get an instance of UserService.

    :return: UserService - instance of UserService.
    """
    return UserService()


def get_message_queue_service() -> MessageQueueService:
    """
    Dependency to get an instance of MessageQueueService.

    :return: MessageQueueService - instance of MessageQueueService.
    """
    return MessageQueueService()


def get_penalty_service() -> PenaltyService:
    """
    Dependency to get an instance of PenaltyService.

    :return: PenaltyService - instance of PenaltyService.
    """
    return PenaltyService()
