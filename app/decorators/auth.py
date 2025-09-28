from functools import wraps
from typing import Callable, Any, Awaitable
from aiogram.types import Message
from aiogram.enums import ChatType

from app.services import UserService, ChatService


class AuthDecorators:
    """
    Класс с декораторами для проверки прав пользователя и регистрации.
    """

    @staticmethod
    def required_creator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        """
        Декоратор для проверки, является ли пользователь создателем бота.
        Если пользователь не является создателем, отправляется сообщение об ошибке.
        :param func: Функция-обработчик команды.
        :return: Обёрнутая функция.
        """
        @wraps(func)
        async def wrapper(self, message: Message, *args, **kwargs) -> Any:
            user_service = UserService()
            user = await user_service.get_user_by_telegram_id(message.from_user.id)

            if not user or not user.is_creator:
                await message.reply(
                    '❌ У вас нет прав для выполнения этой команды.\n'
                    'Только создатель бота может выполнять эту операцию.'
                )
                return

            return await func(self, message, *args, **kwargs)

        return wrapper

    @staticmethod
    def required_admin(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        """
        Декоратор для проверки, является ли пользователь администратором или создателем бота.
        Если пользователь не является администратором или создателем, отправляется сообщение об ошибке.
        :param func: Функция-обработчик команды.
        :return: Обёрнутая функция.
        """
        @wraps(func)
        async def wrapper(self, message: Message, *args, **kwargs) -> Any:
            user_service = UserService()
            user = await user_service.get_user_by_telegram_id(message.from_user.id)

            if not user or not user.is_admin:
                await message.reply(
                    '❌ У вас нет прав для выполнения этой команды.\n'
                    'Только администраторы и создатель бота могут выполнять эту операцию.'
                )
                return

            return await func(self, message, *args, **kwargs)

        return wrapper

    @staticmethod
    def required_user_registration(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        """
        Декоратор для проверки, зарегистрирован ли пользователь в системе.
        Если пользователь не зарегистрирован, отправляется сообщение с инструкцией по регистрации.
        :param func: Функция-обработчик команды.
        :return: Обёрнутая функция.
        """
        @wraps(func)
        async def wrapper(self, message: Message, *args, **kwargs) -> Any:
            user_service = UserService()
            user = await user_service.get_user_by_telegram_id(message.from_user.id)

            if not user:
                await message.reply(
                    '❌ Вы не зарегистрированы в системе.\n'
                    'Пожалуйста, используйте команду '
                    '/reg вместе с вашим позывным для регистрации.'
                )
                return

            return await func(self, message, *args, **kwargs)

        return wrapper

    @staticmethod
    def required_chat_bind(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        """
        Декоратор для проверки, выполняется ли команда исключительно в
        привязанном к боту чате.

        :param func: Функция-обработчик команды.
        :return: Обёрнутая функция.
        """
        @wraps(func)
        async def wrapper(self, message: Message, *args, **kwargs) -> Any:
            chat_service = ChatService()
            chat_exists = await chat_service.get_chat_by_telegram_id(message.chat.id)
            if not chat_exists:
                await message.reply(
                    '❌ Данную команду можно использовать только ' 
                    'в привязанном к боту чате.'
                )
                return

            return await func(self, message, *args, **kwargs)

        return wrapper
    
    @staticmethod
    def required_not_private_chat(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        """
        Декоратор для проверки, что команда выполняется не в приватном чате.

        :param func: Функция-обработчик команды.
        :return: Обёрнутая функция.
        """
        @wraps(func)
        async def wrapper(self, message: Message, *args, **kwargs) -> Any:
            if not hasattr(message, "chat") or message.chat is None:
                await message.reply(
                    '❌ Не удалось определить тип чата для этой команды.'
                )
                return

            if message.chat.type == ChatType.PRIVATE:
                await message.reply(
                    '❌ Данную команду нельзя использовать в приватном чате.'
                )
                return

            return await func(self, message, *args, **kwargs)

        return wrapper
