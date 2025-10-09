import re
import logging
from datetime import datetime
from functools import wraps
from typing import Any, Awaitable, Callable

from aiogram.types import Message

from app.services import MessageQueueService
from app.utils import validate_callsign_format, validate_datetime_format

from config import settings


class CallsignDecorators:
    """
    Class containing decorators for callsign validation.
    Works with methods of classes, not regular functions.
    """

    def __init__(self):
        self.message_queue_service = MessageQueueService()

    @staticmethod
    def validate_callsign_create(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        """
        Decorator for validating callsign in the /reg command.
        Checks that the callsign meets the requirements:
        - Only Latin letters
        - Length from 1 to 20 characters
        - No digits, special characters, or spaces
        - Callsign must be unique
        If the callsign is invalid, sends an error message and does not call the main function

        :param func: Function to be decorated
        :return: Wrapped asynchronous function with the same arguments 
        as the original function
        """

        @wraps(func)
        async def wrapper(self, message: Message, *args: Any, **kwargs: Any) -> Any:
            if not message.text:
                await self.message_queue_service.send_message(
                    chat_id=message.chat.id,
                    text='❌ Неверный формат команды.\n'
                         'Отправь команду `/reg позывной`\n'
                         'Команда не должна содержать ничего, кроме текста!',
                    parse_mode='Markdown',
                    message_id=message.message_id
                )
                return

            command_parts = message.text.split()
            if len(command_parts) != 2:
                await self.message_queue_service.send_message(
                    chat_id=message.chat.id,
                    text='❌ Нужно обязательно написать свой позывной '
                         '(одно слово) '
                         'в текстовом поле после команды.\n\n'
                         'Используйте: `/reg позывной`\n\n'
                         'Требования к позывному:\n'
                         '🔤 Только латинские буквы\n'
                         '📏 Длина от 1 до 20 символов\n'
                         '🚫 Без цифр, спец символов и пробелов\n'
                         '🆔 Позывной должен быть уникальным',
                    parse_mode='Markdown',
                    message_id=message.message_id
                )
                return

            callsign = command_parts[1].strip()

            validation_result = await validate_callsign_format(callsign)
            if not validation_result.is_valid:
                await self.message_queue_service.send_message(
                    chat_id=message.chat.id,
                    text=f'❌ Неверный формат позывного.\n\n'
                         f'{validation_result.error_message}\n\n'
                         f'Используйте: `/reg позывной`\n\n'
                         f'Требования к позывному:\n'
                         f'🔤 Только латинские буквы\n'
                         f'📏 Длина от 1 до 20 символов\n'
                         f'🚫 Без цифр, спец символов и пробелов\n'
                         f'🆔 Позывной должен быть уникальным',
                    parse_mode='Markdown',
                    message_id=message.message_id
                )
                return

            return await func(self, message, callsign, *args, **kwargs)

        return wrapper

    @staticmethod
    def validate_callsign_update(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        """
        Decorator for validating callsign in the /update command.
        If a callsign is provided, checks that it meets the requirements:
        - Only Latin letters
        - Length from 1 to 20 characters
        - No digits, special characters, or spaces
        - Callsign must be unique
        If the callsign is invalid, sends an error message and does not call the main function

        :param func: Function to be decorated
        :return: Wrapped asynchronous function with the same arguments 
        as the original function
        """

        @wraps(func)
        async def wrapper(self, message: Message, *args: Any, **kwargs: Any) -> Any:
            if not message.text:
                await self.message_queue_service.send_message(
                    chat_id=message.chat.id,
                    text='❌ Неверный формат команды.\n'
                         'Отправь команду `/update позывной`\n'
                         'Команда не должна содержать ничего, кроме текста!',
                    parse_mode='Markdown',
                    message_id=message.message_id
                )
                return

            command_parts = message.text.split()

            if len(command_parts) >= 2:

                callsign = command_parts[1].strip()

                validation_result = await validate_callsign_format(callsign)

                if not validation_result.is_valid:
                    await self.message_queue_service.send_message(
                        chat_id=message.chat.id,
                        text=f'❌ Неверный формат позывного.\n\n'
                             f'{validation_result.error_message}\n\n'
                             f'Используйте: `/update позывной`\n\n'
                             f'Требования к позывному:\n'
                             f'🔤 Только латинские буквы\n'
                             f'📏 Длина от 1 до 20 символов\n'
                             f'🚫 Без цифр, спец символов и пробелов\n'
                             f'🆔 Позывной должен быть уникальным',
                        parse_mode='Markdown',
                        message_id=message.message_id
                    )
                    return

            return await func(self, message, *args, **kwargs)

        return wrapper


class SurveyCreationDecorators:
    """
    Class containing decorators for survey creation validation.
    Works with methods of classes, not regular functions.
    """

    def __init__(self):
        self.message_queue_service = MessageQueueService()

    @staticmethod
    def validate_survey_create(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        """
        Decorator for validating survey creation in the /create_survey command.
        Checks that the command parameters meet the requirements:
        - Survey name is not empty and does not exceed 100 characters
        - End date and time are provided in the correct format (YYYY-MM-DD HH:MM)
        - End date and time are in the future
        If the parameters are invalid, sends an error message and does not call the main function

        :param func: Function to be decorated
        :return: Wrapped asynchronous function with the same arguments 
        as the original function
        """
        @wraps(func)
        async def wrapper(self, message: Message, *args: Any, **kwargs: Any) -> Any:
            if not message.text:
                await self.message_queue_service.send_message(
                    chat_id=message.chat.id,
                    text=(
                        '❌ Неверный формат команды.\n'
                        'Отправь команду `/create_survey '
                        'Название_опроса + Время_окончания_опроса `\n'
                        'Команда не должна содержать ничего, кроме текста!'),
                    parse_mode='Markdown',
                    message_id=message.message_id
                )
                return

            text_after_command = message.text[len('/create_survey '):].strip()

            if not text_after_command:
                await self.message_queue_service.send_message(
                    chat_id=message.chat.id,
                    text=(
                        '❌ Команда не может быть выполнена '
                        'так как не были указаны параметры создания опроса.\n\n'
                        'Отправь команду `/create_survey '
                        'Название_опроса + Время_окончания_опроса`\n\n'
                        'Пример правильной команды:\n'
                        '`/create_survey Месим говно 24 часа на броне + 2025-01-01 23:59`\n\n'
                        'Время окончания опроса должно быть в формате\n`YYYY-MM-DD HH:MM`\n'
                        'и быть в будущем.'
                    ),
                    parse_mode='Markdown',
                    message_id=message.message_id
                )
                return

            parts = text_after_command.rsplit(' + ', 1)


            if len(parts) != 2:
                await self.message_queue_service.send_message(
                    chat_id=message.chat.id,
                    text=(
                        '❌ Неверный формат команды.\n'
                        'Отправь команду `/create_survey '
                        'Название_опроса + Время_окончания_опроса`\n\n'
                        'Пример правильной команды:\n'
                        '`/create_survey Месим говно 24 часа на броне + 2025-01-01 23:59`\n\n'
                        'Время окончания опроса должно быть в формате\n`YYYY-MM-DD HH:MM`\n'
                        'и быть в будущем.'
                    ),
                    parse_mode='Markdown',
                    message_id=message.message_id
                )
                return

            survey_name = parts[0].strip()
            end_datetime_str = parts[1].strip()

            if not survey_name:
                await self.message_queue_service.send_message(
                    chat_id=message.chat.id,
                    text=(
                        '❌ Название опроса не может быть пустым.\n'
                        'Отправь команду `/create_survey '
                        'Название_опроса + Время_окончания_опроса`\n\n'
                        'Пример правильной команды:\n'
                        '`/create_survey Месим говно 24 часа на броне + 2025-01-01 23:59`\n\n'
                        'Время окончания опроса должно быть в формате\n`YYYY-MM-DD HH:MM`\n'
                        'и быть в будущем.'),
                    parse_mode='Markdown',
                    message_id=message.message_id
                )
                return

            validation_datetime_result = await validate_datetime_format(end_datetime_str)

            if not validation_datetime_result.is_valid:
                await self.message_queue_service.send_message(
                    chat_id=message.chat.id,
                    text=(
                        f'❌ Неверный формат даты и времени.\n\n'
                        f'{validation_datetime_result.error_message}\n\n'
                        f'Время окончания опроса должно быть в формате\n`YYYY-MM-DD HH:MM`\n'
                        f'и быть в будущем.'),
                    parse_mode='Markdown',
                    message_id=message.message_id
                )
                return

            if len(survey_name) > 100:
                await self.message_queue_service.send_message(
                    chat_id=message.chat.id,
                    text=(
                        '❌ Слишком длинное название опроса.\n\n'
                        'Максимальная длина названия опроса - 100 символов.'),
                    parse_mode='Markdown',
                    message_id=message.message_id
                )
                return
            
            end_datetime = validation_datetime_result.parsed_datetime

            return await func(self, message, survey_name, end_datetime, *args, **kwargs)

        return wrapper
