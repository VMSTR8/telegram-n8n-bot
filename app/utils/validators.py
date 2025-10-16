import re
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.services import UserService
from config import settings


@dataclass
class ValidationResult:
    """
    Result of validation.

    Attributes:
        is_valid (bool): Indicates if the validation was successful.
        error_message (str | None): Error message if validation failed.
        parsed_datetime (datetime | None): Parsed datetime if applicable.
    """
    is_valid: bool
    error_message: str | None = None
    parsed_datetime: datetime | None = None


async def validate_callsign_format(callsign: str) -> ValidationResult:
    """
    Validates the format of a callsign.

    Args:
        callsign (str): The callsign to validate.
    
    Returns:
        ValidationResult: Result of validation.
    """
    user_service: UserService = UserService()

    if not callsign:
        return ValidationResult(
            is_valid=False,
            error_message="Позывной не может быть пустым."
        )

    if len(callsign) > 20:
        return ValidationResult(
            is_valid=False,
            error_message="Позывной не должен превышать 20 символов."
        )

    if not re.match(r'^[a-zA-Z]+$', callsign):
        return ValidationResult(
            is_valid=False,
            error_message="Позывной должен содержать только латинские буквы."
        )

    if await user_service.get_user_by_callsign(callsign.lower()):
        return ValidationResult(
            is_valid=False,
            error_message="Позывной уже занят. Пожалуйста, выберите другой."
        )

    return ValidationResult(is_valid=True)


async def validate_datetime_format(datetime_str: str) -> ValidationResult:
    """
    Validates the format of a datetime string (YYYY-MM-DD HH:MM).

    Args:
        datetime_str (str): The datetime string to validate.
    
    Returns:
        ValidationResult: Result of validation.
    """
    if not datetime_str:
        return ValidationResult(
            is_valid=False,
            error_message='Дата и время не могут быть пустыми.'
        )

    if not re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$', datetime_str):
        return ValidationResult(
            is_valid=False,
            error_message='Используйте правильный шаблон даты\nYYYY-MM-DD HH:MM.'
        )

    try:
        parsed_datetime: datetime = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
        parsed_datetime: datetime = parsed_datetime.replace(tzinfo=settings.timezone_zoneinfo)
    except ValueError:
        return ValidationResult(
            is_valid=False,
            error_message='Неверная дата или время. Убедитесь, что дата существует.'
        )

    if parsed_datetime < datetime.now(tz=settings.timezone_zoneinfo):
        return ValidationResult(
            is_valid=False,
            error_message='Дата и время не могут быть в прошлом.'
        )

    max_future_date: datetime = datetime.now(tz=settings.timezone_zoneinfo) + timedelta(days=180)
    if parsed_datetime > max_future_date:
        return ValidationResult(
            is_valid=False,
            error_message='Максимальный срок действия опроса - 6 месяцев.'
        )

    return ValidationResult(is_valid=True, parsed_datetime=parsed_datetime)
