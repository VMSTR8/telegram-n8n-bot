from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.models import User
from app.utils.validators import validate_callsign_format, validate_datetime_format, ValidationResult


@pytest.mark.unit
@pytest.mark.asyncio
class TestValidatorCallsignFormat:
    """Tests for the validate_callsign_format function."""

    async def test_empty_callsign(self, db: None):
        """Test that an empty callsign returns ValidationResult False."""
        result: ValidationResult = await validate_callsign_format('')

        assert result.is_valid is False
        assert result.error_message == 'Позывной не может быть пустым.'
        assert result.parsed_datetime is None

    async def test_callsign_too_long(self, db: None):
        """Test that a callsign exceeding max length returns ValidationResult False."""
        long_callsign = 'A' * 21
        result: ValidationResult = await validate_callsign_format(long_callsign)

        assert result.is_valid is False
        assert result.error_message == 'Позывной не должен превышать 20 символов.'
        assert result.parsed_datetime is None

    async def test_callsign_invalid_characters(self, db: None):
        """Test that a callsign with invalid characters returns ValidationResult False."""
        result: ValidationResult = await validate_callsign_format('test123')

        assert result.is_valid is False
        assert result.error_message == 'Позывной должен содержать только латинские буквы.'
        assert result.parsed_datetime is None

    async def test_callsign_invalid_characters_special(self, db: None):
        """Test that a callsign with special characters returns ValidationResult False."""
        result: ValidationResult = await validate_callsign_format('test!')

        assert result.is_valid is False
        assert result.error_message == 'Позывной должен содержать только латинские буквы.'
        assert result.parsed_datetime is None

    async def test_callsign_invalid_cyrillic(self, db: None):
        """Test that a callsign with Cyrillic characters returns ValidationResult False."""
        result: ValidationResult = await validate_callsign_format('тест')

        assert result.is_valid is False
        assert result.error_message == 'Позывной должен содержать только латинские буквы.'
        assert result.parsed_datetime is None

    async def test_callsign_already_taken(self, db: None, test_user_regular: User):
        """Test on taken callsign."""
        result: ValidationResult = await validate_callsign_format('regular')

        assert result.is_valid is False
        assert result.error_message == 'Позывной уже занят. Пожалуйста, выберите другой.'
        assert result.parsed_datetime is None

    async def test_callsign_available(self, db: None, test_user_regular: User):
        """Test on available callsign."""
        result: ValidationResult = await validate_callsign_format('valid')

        assert result.is_valid is True
        assert result.error_message is None
        assert result.parsed_datetime is None

    async def test_callsign_case_insensitive_taken(self, db: None, test_user_regular: User):
        """Test on taken callsign with case insensitivity."""
        result: ValidationResult = await validate_callsign_format('REGULAR')

        assert result.is_valid is False
        assert result.error_message == 'Позывной уже занят. Пожалуйста, выберите другой.'
        assert result.parsed_datetime is None

    async def test_callsign_case_insensitive_available(self, db: None, test_user_regular: User):
        """Test on available callsign with case insensitivity."""
        result: ValidationResult = await validate_callsign_format('VaLiD')

        assert result.is_valid is True
        assert result.error_message is None
        assert result.parsed_datetime is None

    async def test_callsign_max_length_available(self, db: None):
        """Test on available callsign with max length."""
        max_length_callsign = 'A' * 20
        result: ValidationResult = await validate_callsign_format(max_length_callsign)

        assert result.is_valid is True
        assert result.error_message is None
        assert result.parsed_datetime is None


@pytest.mark.unit
@pytest.mark.asyncio
class TestValidatorDatetimeFormat:
    """Tests for the validate_datetime_format function."""

    async def test_empty_datetime(self):
        """Test that an empty datetime string returns ValidationResult False."""
        result: ValidationResult = await validate_datetime_format('')

        assert result.is_valid is False
        assert result.error_message == 'Дата и время не могут быть пустыми.'
        assert result.parsed_datetime is None

    async def test_invalid_format_slash_separator(self):
        """Test that an invalid datetime format returns ValidationResult False."""

        result: ValidationResult = await validate_datetime_format('2023/10/01 12:00')
        assert result.is_valid is False
        assert result.error_message == 'Используйте правильный шаблон даты\nYYYY-MM-DD HH:MM.'
        assert result.parsed_datetime is None

    async def test_invalid_format_extra_seconds(self):
        """Test that a datetime with extra seconds returns ValidationResult False."""
        result: ValidationResult = await validate_datetime_format('2023-10-01 12:00:00')

        assert result.is_valid is False
        assert result.error_message == 'Используйте правильный шаблон даты\nYYYY-MM-DD HH:MM.'
        assert result.parsed_datetime is None

    async def test_invalid_format_missing_time(self):
        """Test that a datetime missing time returns ValidationResult False."""
        result: ValidationResult = await validate_datetime_format('2023-10-01')

        assert result.is_valid is False
        assert result.error_message == 'Используйте правильный шаблон даты\nYYYY-MM-DD HH:MM.'
        assert result.parsed_datetime is None

    async def test_invalid_date_february_30(self):
        """Test that February 30th returns ValidationResult False."""
        result: ValidationResult = await validate_datetime_format('2023-02-30 12:00')

        assert result.is_valid is False
        assert result.error_message == 'Неверная дата или время. Убедитесь, что дата существует.'
        assert result.parsed_datetime is None

    async def test_invalid_date_month_13(self):
        """Test that month 13 returns ValidationResult False."""
        result: ValidationResult = await validate_datetime_format('2023-13-01 12:00')

        assert result.is_valid is False
        assert result.error_message == 'Неверная дата или время. Убедитесь, что дата существует.'
        assert result.parsed_datetime is None

    async def test_invalid_time_hour_25(self):
        """Test that hour 25 returns ValidationResult False."""
        result: ValidationResult = await validate_datetime_format('2023-10-01 25:00')

        assert result.is_valid is False
        assert result.error_message == 'Неверная дата или время. Убедитесь, что дата существует.'
        assert result.parsed_datetime is None

    async def test_past_datetime(self, moscow_timezone: ZoneInfo):
        """Test that a past datetime returns ValidationResult False."""
        past_date: str = (
                datetime.now(tz=moscow_timezone) - timedelta(hours=1)
        ).strftime('%Y-%m-%d %H:%M')
        result: ValidationResult = await validate_datetime_format(past_date)

        assert result.is_valid is False
        assert result.error_message == 'Дата и время не могут быть в прошлом.'
        assert result.parsed_datetime is None

    async def test_datetime_too_far_in_future(self, moscow_timezone: ZoneInfo):
        """Test that a datetime too far in the future returns ValidationResult False."""
        future_date: str = (
                datetime.now(tz=moscow_timezone) + timedelta(days=181)
        ).strftime('%Y-%m-%d %H:%M')
        result: ValidationResult = await validate_datetime_format(future_date)

        assert result.is_valid is False
        assert result.error_message == 'Максимальный срок действия опроса - 6 месяцев.'
        assert result.parsed_datetime is None

    async def test_valid_datetime_30_days(self, moscow_timezone: ZoneInfo):
        """Test that a datetime 30 days in the future returns ValidationResult True."""
        valid_date: str = (
                datetime.now(tz=moscow_timezone) + timedelta(days=30)
        ).strftime('%Y-%m-%d %H:%M')
        result: ValidationResult = await validate_datetime_format(valid_date)

        assert result.is_valid is True
        assert result.error_message is None
        assert result.parsed_datetime is not None
        assert isinstance(result.parsed_datetime, datetime)
        assert result.parsed_datetime.tzinfo == moscow_timezone

    async def test_valid_datetime_edge_180_days(self, moscow_timezone: ZoneInfo):
        """Test that a datetime exactly 6 months in the future returns ValidationResult True."""
        edge_date: str = (
                datetime.now(tz=moscow_timezone) + timedelta(days=180)
        ).strftime('%Y-%m-%d %H:%M')
        result: ValidationResult = await validate_datetime_format(edge_date)

        assert result.is_valid is True
        assert result.error_message is None
        assert result.parsed_datetime is not None
        assert isinstance(result.parsed_datetime, datetime)

    async def test_valid_datetime_tomorrow(self, moscow_timezone: ZoneInfo):
        """Test that a datetime tomorrow returns ValidationResult True."""
        tomorrow_date: str = (
                datetime.now(tz=moscow_timezone) + timedelta(days=1)
        ).strftime('%Y-%m-%d %H:%M')
        result: ValidationResult = await validate_datetime_format(tomorrow_date)

        assert result.is_valid is True
        assert result.error_message is None
        assert result.parsed_datetime is not None
        assert isinstance(result.parsed_datetime, datetime)

    async def test_valid_datetime_1_hour_future(self, moscow_timezone: ZoneInfo):
        """Test that a datetime 1 hour in the future returns ValidationResult True."""
        future_date: str = (
                datetime.now(tz=moscow_timezone) + timedelta(hours=1)
        ).strftime('%Y-%m-%d %H:%M')
        result: ValidationResult = await validate_datetime_format(future_date)

        assert result.is_valid is True
        assert result.error_message is None
        assert result.parsed_datetime is not None
        assert isinstance(result.parsed_datetime, datetime)
        assert result.parsed_datetime > datetime.now(tz=moscow_timezone)
