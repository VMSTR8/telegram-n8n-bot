import logging
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.bot_telegram import (
    init_database,
    close_database,
    BotManager
)
from .webhook import telegram_webhook_router
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
        bot_manager = BotManager()
        await bot_manager.ensure_creator_exists()
        bot = bot_manager.create_bot()
        webhook_url = f'{settings.telegram.webhook_url}/webhook'
        await bot.set_webhook(
            url=webhook_url,
            secret_token=settings.telegram.webhook_secret
        )
        logging.info(f'Webhook successfully set at: {webhook_url}')
        app.state.bot_manager = bot_manager
    except Exception as e:
        logging.error(f'Error occurred while setting webhook: {e}')

    logging.info('Application started successfully in webhook mode.')

    yield

    # Shutdown
    # TODO: This siece of phit does not work properly. Need to find a way to handle SIGTERM correctly.
    try:
        bot_manager = getattr(app.state, 'bot_manager', None)
        if bot_manager and bot_manager.bot:
            await bot_manager.bot.delete_webhook(drop_pending_updates=True)
            await bot_manager.bot.session.close()
            logging.info('Webhook deleted and bot session closed.')

        await close_database()
        logging.info('Database connection closed successfully.')

    except Exception as e:
        logging.error(f'Error occurred during shutdown: {e}')


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

    app.include_router(telegram_webhook_router, tags=['webhook'])

    return app


telegrambot_app = create_app()
