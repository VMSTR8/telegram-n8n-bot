from functools import wraps
from typing import Callable, Any, Awaitable
from aiogram.types import Message
from app.utils import validate_callsign_format


def validate_callsign_create(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
    """
    Декоратор для валидации позывного в команде /reg.
    Проверяет, что позывной соответствует требованиям:
    - Только латинские буквы
    - Длина от 1 до 20 символов
    - Без цифр, спец символов и пробелов
    - Позывной должен быть уникальным (проверка в самой функции)
    Если позывной невалиден, отправляет сообщение с ошибкой и не вызывает основную функцию.
    :param func: Функция, которую декорируем
    :return: Обернутая функция
    """
    @wraps(func)
    async def wrapper(self, message: Message, *args: Any, **kwargs: Any) -> Any:

        if not message.text:
            await message.reply(
                text='❌ Неверный формат команды.\n'
                     'Отправь команду `/reg позывной`\n'
                     'Команда не должна содержать ничего, кроме текста!',
                parse_mode='Markdown'
            )
            return

        command_parts = message.text.split()
        if len(command_parts) != 2:
            await message.reply(
                text='❌ Нужно обязательно написать свой позывной '
                     '(одно слово) '
                     'в текстовом поле после команды.\n\n'
                     'Используйте: `/reg позывной`\n\n'
                     'Требования к позывному:\n'
                     '🔤 Только латинские буквы\n'
                     '📏 Длина от 1 до 20 символов\n'
                     '🚫 Без цифр, спец символов и пробелов\n'
                     '🆔 Позывной должен быть уникальным',
                parse_mode='Markdown'
            )
            return
        callsign = command_parts[1].strip()

        validation_result = validate_callsign_format(callsign)
        if not validation_result.is_valid:
            await message.reply(
                text=f'❌ Неверный формат позывного.\n\n'
                     f'{validation_result.error_message}\n\n'
                     f'Используйте: `/reg позывной`\n\n'
                     f'Требования к позывному:\n'
                     f'🔤 Только латинские буквы\n'
                     f'📏 Длина от 1 до 20 символов\n'
                     f'🚫 Без цифр, спец символов и пробелов\n'
                     f'🆔 Позывной должен быть уникальным',
                parse_mode='Markdown'
            )
            return

        return await func(self, message, callsign, *args, **kwargs)

    return wrapper
