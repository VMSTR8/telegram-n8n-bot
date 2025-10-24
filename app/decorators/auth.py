from functools import wraps
from typing import Awaitable, Callable, TypeVar

from aiogram.enums import ChatType
from aiogram.types import Message

from app.models import User, Chat
from app.services import UserService, ChatService, MessageQueueService

T = TypeVar('T')


class AuthDecorators:
    """
    Class containing decorators for authentication checks.
    
    Attributes:
        message_queue_service: Instance of MessageQueueService for sending messages.

    Methods:
        required_creator: Decorator to check if the user is the bot creator.
        required_admin: Decorator to check if the user is an administrator or the bot creator.
        required_user_registration: Decorator to check if the user is registered in the system.
        required_chat_bind: Decorator to check if the command is executed in a bound chat.
        required_not_private_chat: Decorator to check if the command is executed in a non-private chat.
    """

    def __init__(self):
        self.message_queue_service: MessageQueueService = MessageQueueService()

    @staticmethod
    def required_creator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T | None]]:
        """
        Decorator to check if the user is the bot creator.
        If the user is not the creator, an error message is sent.

        Args:
            func: Function to be decorated.

        Returns:
            Wrapped asynchronous function with the same arguments as the original function.
        """

        @wraps(func)
        async def wrapper(self, message: Message, *args, **kwargs) -> T | None:
            user_service: UserService = UserService()
            user: User = await user_service.get_user_by_telegram_id(message.from_user.id)

            if not user or not user.is_creator:
                await self.message_queue_service.send_message(
                    chat_id=message.chat.id,
                    text='❌ У вас нет прав для выполнения этой команды.\n'
                         'Только создатель бота может выполнять эту операцию.',
                    parse_mode='Markdown',
                    message_id=message.message_id
                )
                return None

            return await func(self, message, *args, **kwargs)

        return wrapper

    @staticmethod
    def required_admin(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        """
        Decorator to check if the user is an administrator or the bot creator.
        If the user is not an admin or creator, an error message is sent.

        Args:
            func: Function to be decorated.

        Returns:
            Wrapped asynchronous function with the same arguments as the original function.
        """

        @wraps(func)
        async def wrapper(self, message: Message, *args, **kwargs) -> T:
            user_service: UserService = UserService()
            user: User = await user_service.get_user_by_telegram_id(message.from_user.id)

            if not user or not user.is_admin:
                await self.message_queue_service.send_message(
                    chat_id=message.chat.id,
                    text='❌ У вас нет прав для выполнения этой команды.\n'
                         'Только администраторы и создатель бота могут выполнять эту операцию.',
                    parse_mode='Markdown',
                    message_id=message.message_id
                )
                return None

            return await func(self, message, *args, **kwargs)

        return wrapper

    @staticmethod
    def required_user_registration(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T | None]]:
        """
        Decorator to check if the user is registered in the system.
        If the user is not registered, an error message is sent.

        Args:
            func: Function to be decorated.

        Returns:
            Wrapped asynchronous function with the same arguments as the original function.
        """

        @wraps(func)
        async def wrapper(self, message: Message, *args, **kwargs) -> T:
            user_service: UserService = UserService()
            user: User = await user_service.get_user_by_telegram_id(message.from_user.id)

            if not user:
                await self.message_queue_service.send_message(
                    chat_id=message.chat.id,
                    text='❌ Вы не зарегистрированы в системе.\n'
                         'Пожалуйста, используйте команду '
                         '/reg вместе с вашим позывным для регистрации.',
                    parse_mode='Markdown',
                    message_id=message.message_id
                )
                return None

            return await func(self, message, *args, **kwargs)

        return wrapper

    @staticmethod
    def required_chat_bind(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T | None]]:
        """
        Decorator to check if the command is executed in a chat that is bound to the bot.
        If the chat is not bound, an error message is sent.

        Args:
            func: Function to be decorated.

        Returns:
            Wrapped asynchronous function with the same arguments as the original function.
        """

        @wraps(func)
        async def wrapper(self, message: Message, *args, **kwargs) -> T:
            chat_service: ChatService = ChatService()
            chat_exists: Chat | None = await chat_service.get_chat_by_telegram_id(message.chat.id)
            if not chat_exists:
                await self.message_queue_service.send_message(
                    chat_id=message.chat.id,
                    text='❌ Данную команду можно использовать только '
                         'в привязанном к боту чате.',
                    parse_mode='Markdown',
                    message_id=message.message_id
                )
                return None

            return await func(self, message, *args, **kwargs)

        return wrapper

    @staticmethod
    def required_not_private_chat(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T | None]]:
        """
        Decorator to check if the command is executed in a chat that is not private.

        Args:
            func: Function to be decorated.

        Returns:
            Wrapped asynchronous function with the same arguments as the original function.
        """

        @wraps(func)
        async def wrapper(self, message: Message, *args, **kwargs) -> T | None:
            if not hasattr(message, "chat") or message.chat is None:
                await self.message_queue_service.send_message(
                    chat_id=message.chat.id,
                    text='❌ Не удалось определить тип чата для этой команды.',
                    parse_mode='Markdown',
                    message_id=message.message_id
                )
                return None

            if message.chat.type == ChatType.PRIVATE:
                await self.message_queue_service.send_message(
                    chat_id=message.chat.id,
                    text='❌ Данную команду нельзя использовать в приватном чате.',
                    parse_mode='Markdown',
                    message_id=message.message_id
                )
                return None

            return await func(self, message, *args, **kwargs)

        return wrapper
