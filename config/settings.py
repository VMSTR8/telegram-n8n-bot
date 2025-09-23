from typing import Optional
from zoneinfo import ZoneInfo
from pydantic import Field, PrivateAttr
from pydantic_settings import BaseSettings


class TelegramBotSettings(BaseSettings):
    """Настройки для Telegram бота"""
    bot_token: Optional[str] = Field(default=None, description='Токен для бота')
    creator_id: Optional[int] = Field(default=None, description='Telegram ID создателя бота')
    webhook_url: Optional[str] = Field(default=None, description='URL для webhook')
    webhook_secret: Optional[str] = Field(default=None, description='Секретный ключ для webhook')


class DatabaseSettings(BaseSettings):
    """Настройки для базы данных"""
    host: str = Field(default='localhost', description='Хост базы данных')
    port: int = Field(default=5432, description='Порт базы данных')
    user: str = Field(default='postgres', description='Пользователь базы данных')
    password: str = Field(default='password', description='Пароль базы данных')
    basename: str = Field(default='telegramBot', description='Имя базы данных')

    @property
    def url(self) -> str:
        return f'postgres://{self.user}:{self.password}@{self.host}:{self.port}/{self.basename}'


class AppSettings(BaseSettings):
    """Основные настройки приложения"""
    timezone: str = Field(default='Europe/Moscow', description='Часовой пояс приложения', exclude=True)
    telegram: TelegramBotSettings = Field(default_factory=TelegramBotSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)

    @property
    def timezone_zoneinfo(self) -> ZoneInfo:
        """
        Возвращает объект ZoneInfo для часового пояса приложения
        :return: ZoneInfo объект
        """
        return ZoneInfo(self.timezone)

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        extra = 'ignore'
        env_nested_delimiter = '__'


settings = AppSettings()
