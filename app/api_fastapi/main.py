import logging
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.bot_telegram import (
    init_database,
    close_database,
    BotManager
)
from config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Context manager for application lifespan events.

    :param app: FastAPI - FastAPI application instance
    :return: AsyncGenerator[None, None] - asynchronous generator.
    """
    logging.info('Starting application in production mode...')

    try:
        await init_database()
        logging.info('Database initialized successfully.')
    except Exception as e:
        logging.error(f'Error occurred during database initialization: {e}')
        raise

    try:
        bot = BotManager().create_bot()
        webhook_url = f'{settings.telegram.webhook_url}/webhook'
        await bot.set_webhook(
            url=webhook_url,
            secret_token=settings.telegram.webhook_secret
        )
        logging.info(f'Webhook successfully set at: {webhook_url}')
    except Exception as e:
        logging.error(f'Error occurred while setting webhook: {e}')

    logging.info('Application started successfully.')

    yield

    # TODO: Implement graceful shutdown for the bot


def create_app() -> FastAPI:
    """
    Creates an instance of the FastAPI application.

    :return: FastAPI - FastAPI application instance.
    """
    app = FastAPI(
        title='Telegram Bot with n8n integration',
        description='API для управления Telegram ботом с интеграцией n8n',
        version='1.0.0',
        docs_url='/docs',
        redoc_url='/redoc',
        redirect_slashes=False,
        lifespan=lifespan
    )

    # TODO: Add routes, middleware, exception handlers, etc.

    return app
