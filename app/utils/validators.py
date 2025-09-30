import re
from dataclasses import dataclass
from typing import Optional
from app.services import UserService


@dataclass
class ValidationResult:
    """
    Result of validation.
    """
    is_valid: bool
    error_message: Optional[str] = None


async def validate_callsign_format(callsign: str) -> ValidationResult:
    """
    Validates the format of a callsign.

    :param callsign: The callsign to validate.
    :return: ValidationResult - result of validation.
    """
    user_service = UserService()

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
