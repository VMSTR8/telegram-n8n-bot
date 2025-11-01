from zoneinfo import ZoneInfo

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class TelegramBotSettings(BaseSettings):
    """Settings for the Telegram bot"""
    bot_token: str | None = Field(default=None, description='Bot token')
    creator_id: int | None = Field(default=None, description='Telegram ID of the bot creator')
    webhook_url: str | None = Field(default=None, description='Webhook URL')
    webhook_secret: str | None = Field(default=None, description='Webhook secret key')


class DatabaseSettings(BaseSettings):
    """Settings for the database connection"""
    host: str = Field(default='localhost', description='Database host')
    port: int = Field(default=5432, description='Database port')
    user: str = Field(default='telegram_n8n_db', description='Database user')
    password: str = Field(default='reallyhardpassword0432', description='Database password')
    basename: str = Field(default='telegram_n8n_db', description='Database name')

    @property
    def url(self) -> str:
        return f'postgres://{self.user}:{self.password}@{self.host}:{self.port}/{self.basename}'


class RabbitMQSettings(BaseSettings):
    """Settings for RabbitMQ connection"""
    host: str = Field(default='rabbitmq', description='RabbitMQ host')
    port: int = Field(default=5672, description='RabbitMQ port')
    user: str = Field(default='admin', description='RabbitMQ user')
    password: str = Field(default='password', description='RabbitMQ password')

    @property
    def url(self) -> str:
        return f'amqp://{self.user}:{self.password}@{self.host}:{self.port}//'


class N8NSettings(BaseSettings):
    """Settings for n8n connection"""
    n8n_webhook_url: str | None = Field(default=None, description='n8n webhook URL')
    n8n_webhook_header: str | None = Field(default=None, description='n8n webhook header key')
    n8n_webhook_secret: str | None = Field(default=None, description='n8n webhook secret key')


class ServiceSettings(BaseSettings):
    """Settings for external services"""
    bot_service: str = Field(default='http://api:8000', description='URL of the internal bot service')
    n8n_service: str = Field(default='http://n8n:5678', description='URL of the internal n8n service')


class AppSettings(BaseSettings):
    """Main application settings"""
    timezone: str = Field(default='Europe/Moscow', description='Application timezone', exclude=True)
    polling_mode: bool = Field(default=True, description='Enable polling mode instead of webhook')
    telegram: TelegramBotSettings = Field(default_factory=TelegramBotSettings)
    n8n: N8NSettings = Field(default_factory=N8NSettings)
    services: ServiceSettings = Field(default_factory=ServiceSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    rabbitmq: RabbitMQSettings = Field(default_factory=RabbitMQSettings)

    @property
    def timezone_zoneinfo(self) -> ZoneInfo:
        """
        Returns the timezone as a ZoneInfo object.

        Returns:
            ZoneInfo: Timezone information
        """
        return ZoneInfo(self.timezone)

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
        env_nested_delimiter='__'
    )


settings = AppSettings()
