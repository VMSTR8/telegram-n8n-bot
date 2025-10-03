from functools import wraps
from typing import Any, Awaitable, Callable

from aiogram.enums import ChatType
from aiogram.types import Message

from app.services import UserService, ChatService, MessageQueueService


class AuthDecorators:
    """
    Class containing decorators for authentication checks.
    """

    def __init__(self):
        self.message_queue_service = MessageQueueService()

    @staticmethod
    def required_creator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        """
        Decorator to check if the user is the bot creator.
        If the user is not the creator, an error message is sent.

        :param func: Function to be decorated.
        :return: Wrapped asynchronous function with the same arguments as the original function.
        """

        @wraps(func)
        async def wrapper(self, message: Message, *args, **kwargs) -> Any:
            user_service = UserService()
            user = await user_service.get_user_by_telegram_id(message.from_user.id)

            if not user or not user.is_creator:
                await self.message_queue_service.send_message(
                    chat_id=message.chat.id,
                    text='❌ У вас нет прав для выполнения этой команды.\n'
                         'Только создатель бота может выполнять эту операцию.'
                )
                return

            return await func(self, message, *args, **kwargs)

        return wrapper

    @staticmethod
    def required_admin(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        """
        Decorator to check if the user is an administrator or the bot creator.
        If the user is not an admin or creator, an error message is sent.

        :param func: Function to be decorated.
        :return: Wrapped asynchronous function with the same arguments as the original function.
        """

        @wraps(func)
        async def wrapper(self, message: Message, *args, **kwargs) -> Any:
            user_service = UserService()
            user = await user_service.get_user_by_telegram_id(message.from_user.id)

            if not user or not user.is_admin:
                await self.message_queue_service.send_message(
                    chat_id=message.chat.id,
                    text='❌ У вас нет прав для выполнения этой команды.\n'
                         'Только администраторы и создатель бота могут выполнять эту операцию.'
                )
                return

            return await func(self, message, *args, **kwargs)

        return wrapper

    @staticmethod
    def required_user_registration(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        """
        Decorator to check if the user is registered in the system.
        If the user is not registered, an error message is sent.

        :param func: Function to be decorated.
        :return: Wrapped asynchronous function with the same arguments as the original function.
        """

        @wraps(func)
        async def wrapper(self, message: Message, *args, **kwargs) -> Any:
            user_service = UserService()
            user = await user_service.get_user_by_telegram_id(message.from_user.id)

            if not user:
                await self.message_queue_service.send_message(
                    chat_id=message.chat.id,
                    text='❌ Вы не зарегистрированы в системе.\n'
                         'Пожалуйста, используйте команду '
                         '/reg вместе с вашим позывным для регистрации.'
                )
                return

            return await func(self, message, *args, **kwargs)

        return wrapper

    @staticmethod
    def required_chat_bind(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        """
        Decorator to check if the command is executed in a chat that is bound to the bot.
        If the chat is not bound, an error message is sent.

        :param func: Function to be decorated.
        :return: Wrapped asynchronous function with the same arguments as the original function.
        """

        @wraps(func)
        async def wrapper(self, message: Message, *args, **kwargs) -> Any:
            chat_service = ChatService()
            chat_exists = await chat_service.get_chat_by_telegram_id(message.chat.id)
            if not chat_exists:
                await self.message_queue_service.send_message(
                    chat_id=message.chat.id,
                    text='❌ Данную команду можно использовать только '
                         'в привязанном к боту чате.'
                )
                return

            return await func(self, message, *args, **kwargs)

        return wrapper

    @staticmethod
    def required_not_private_chat(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        """
        Decorator to check if the command is executed in a chat that is not private.

        :param func: Function to be decorated.
        :return: Wrapped asynchronous function with the same arguments as the original function.
        """

        @wraps(func)
        async def wrapper(self, message: Message, *args, **kwargs) -> Any:
            if not hasattr(message, "chat") or message.chat is None:
                await self.message_queue_service.send_message(
                    chat_id=message.chat.id,
                    text='❌ Не удалось определить тип чата для этой команды.'
                )
                return

            if message.chat.type == ChatType.PRIVATE:
                await self.message_queue_service.send_message(
                    chat_id=message.chat.id,
                    text='❌ Данную команду нельзя использовать в приватном чате.'
                )
                return

            return await func(self, message, *args, **kwargs)

        return wrapper
