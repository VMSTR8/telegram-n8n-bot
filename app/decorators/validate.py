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
        command_parts = message.text.split()
        if len(command_parts) < 2:
            await message.reply(
                '❌ Неверный формат команды.\n'
                'Используйте: /reg ваш_позывной\n'
                'Требования к позывному:\n'
                '• Только латинские буквы'
                '• Длина от 1 до 20 символов\n'
                '• Без цифр, спец символов и пробелов\n'
                '• Позывной должен быть уникальным'
            )
            return
        callsign = command_parts[1].strip()

        validation_result = validate_callsign_format(callsign)
        if not validation_result.is_valid:
            await message.reply(
                '❌ Неверный формат команды.\n'
                'Используйте: /reg ваш_позывной\n\n'
                'Требования к позывному:\n'
                '• Только латинские буквы'
                '• Длина от 1 до 20 символов\n'
                '• Без цифр, спец символов и пробелов\n'
                '• Позывной должен быть уникальным'
            )
            return

        return await func(self, message, *args, **kwargs)

    return wrapper
