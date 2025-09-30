from typing import Optional
from zoneinfo import ZoneInfo
from pydantic import Field, PrivateAttr
from pydantic_settings import BaseSettings


class TelegramBotSettings(BaseSettings):
    """Settings for the Telegram bot"""
    bot_token: Optional[str] = Field(default=None, description='Bot token')
    creator_id: Optional[int] = Field(default=None, description='Telegram ID of the bot creator')
    webhook_url: Optional[str] = Field(default=None, description='Webhook URL')
    webhook_secret: Optional[str] = Field(default=None, description='Webhook secret key')


class DatabaseSettings(BaseSettings):
    """Settings for the database connection"""
    host: str = Field(default='localhost', description='Database host')
    port: int = Field(default=5432, description='Database port')
    user: str = Field(default='postgres', description='Database user')
    password: str = Field(default='password', description='Database password')
    basename: str = Field(default='telegramBot', description='Database name')

    @property
    def url(self) -> str:
        return f'postgres://{self.user}:{self.password}@{self.host}:{self.port}/{self.basename}'

class RabbitMQSettings(BaseSettings):
    """Settings for RabbitMQ connection"""
    rmq_host: str = Field(default='localhost', description='RabbitMQ host')
    rmq_port: int = Field(default=5672, description='RabbitMQ port')
    rmq_user: str = Field(default='admin', description='RabbitMQ user')
    rmq_password: str = Field(default='definitelynotanadminpassword', description='RabbitMQ password')
    rmq_vhost: str = Field(default='/telegram_bot', description='RabbitMQ virtual host')

    @property
    def url(self) -> str:
        return (
            f"amqp://{self.rmq_user}:{self.rmq_password}"
            f"@{self.rmq_host}:{self.rmq_port}"
            f"{self.rmq_vhost}"
        )


class AppSettings(BaseSettings):
    """Main application settings"""
    timezone: str = Field(default='Europe/Moscow', description='Application timezone', exclude=True)
    polling_mode: bool = Field(default=True, description='Enable polling mode instead of webhook')
    telegram: TelegramBotSettings = Field(default_factory=TelegramBotSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    rabbitmq: RabbitMQSettings = Field(default_factory=RabbitMQSettings)

    @property
    def timezone_zoneinfo(self) -> ZoneInfo:
        """
        Returns the timezone as a ZoneInfo object.

        :return: ZoneInfo object corresponding to the configured timezone
        """
        return ZoneInfo(self.timezone)

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        extra = 'ignore'
        env_nested_delimiter = '__'


settings = AppSettings()
