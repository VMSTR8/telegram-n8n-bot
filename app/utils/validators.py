import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class ValidationResult:
    """
    Результат валидации.
    """
    is_valid: bool
    error_message: Optional[str] = None


def validate_callsign_format(callsign: str) -> ValidationResult:
    """
    Валидирует формат позывного.
    :param callsign: Позывной для валидации.
    :return: ValidationResult - результат валидации.
    """
    if not callsign:
        return ValidationResult(
            is_valid=False,
            error_message="Позывной не может быть пустым."
        )

    if len(callsign) < 1:
        return ValidationResult(
            is_valid=False,
            error_message="Позывной должен содержать не менее 1 символа."
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

    return ValidationResult(is_valid=True)
