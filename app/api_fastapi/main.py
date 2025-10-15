import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from aiogram import Bot

from app.api_fastapi.routers import telegram_webhook_router, n8n_webhook_router
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
        bot_manager: BotManager = BotManager()
        await bot_manager.ensure_creator_exists()
        
        bot: Bot = bot_manager.create_bot()
        
        webhook_url: str = f'{settings.telegram.webhook_url}/webhook'
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
    try:
        bot_manager: BotManager = getattr(app.state, 'bot_manager', None)
        
        if bot_manager and bot_manager.bot:
            await bot_manager.bot.delete_webhook(drop_pending_updates=True)
            await bot_manager.bot.session.close()
            logging.info('Webhook deleted and bot session closed.')

        await close_database()
        logging.info('Database closed successfully.')

    except Exception as e:
        logging.error(f'Error occurred during shutdown: {e}')


def create_app() -> FastAPI:
    """
    Creates an instance of the FastAPI application.

    :return: FastAPI - FastAPI application instance.
    """
    app: FastAPI = FastAPI(
        title='Telegram Bot with n8n integration',
        description='A FastAPI application that integrates a Telegram bot with n8n workflow automation.',
        version='1.0.0',
        docs_url='/docs',
        redoc_url='/redoc',
        redirect_slashes=False,
        lifespan=lifespan
    )

    app.include_router(telegram_webhook_router, tags=['telegram_webhook'])
    app.include_router(n8n_webhook_router, tags=['n8n_webhook'])

    return app


telegrambot_app: FastAPI = create_app()
