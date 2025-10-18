import logging
import traceback
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from aiogram import Bot
from fastapi import FastAPI

from app.api_fastapi.routers import telegram_webhook_router, n8n_webhook_router
from app.bot_telegram import (
    init_database,
    close_database,
    BotManager
)
from config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Context manager for application lifespan events.

    Args:
        app (FastAPI): The FastAPI application instance.
    
    Raises:
        Exception: If any error occurs during startup or shutdown.
    
    Yields:
        Shuts down the application context.
    
    Returns:
        None
    """
    logger.info('Starting FastAPI application in production mode...')

    try:
        await init_database()
        logger.info('Database initialized successfully.')
    except Exception as e:
        logger.error('Failed to initialize database: %s\n%s', str(e), traceback.format_exc())
        raise

    try:
        bot_manager: BotManager = BotManager()
        await bot_manager.ensure_creator_exists()
        logger.info('Bot manager initialized and creator verified.')

        bot: Bot = bot_manager.create_bot()

        webhook_url: str = f'{settings.telegram.webhook_url}/webhook'
        await bot.set_webhook(
            url=webhook_url,
            secret_token=settings.telegram.webhook_secret,
            allowed_updates=['message', 'edited_message', 'callback_query']
        )
        logger.info('Webhook set successfully at URL: %s', webhook_url)

        app.state.bot_manager = bot_manager
        logger.info('Application started successfully in webhook mode.')

    except Exception as e:
        logger.error('Error occurred while setting webhook: %s\n%s', str(e), traceback.format_exc())
        if bot_manager and bot_manager.bot:
            try:
                await bot_manager.bot.delete_webhook(drop_pending_updates=True)
                await bot_manager.bot.session.close()
                logger.info('Cleaned up bot resources after failure.')
            except Exception as e:
                logger.error('Failed to clean up bot resources: %s\n%s', str(e), traceback.format_exc())
        raise

    yield

    # Shutdown
    logger.info('Shutting down FastAPI application...')
    try:
        bot_manager: BotManager = getattr(app.state, 'bot_manager', None)

        if bot_manager and bot_manager.bot:
            await bot_manager.bot.delete_webhook(drop_pending_updates=True)
            await bot_manager.bot.session.close()
            logger.info('Webhook deleted and bot session closed successfully.')

        await close_database()
        logger.info('Database closed successfully.')

    except Exception as e:
        logger.error('Error during shutdown: %s\n%s', str(e), traceback.format_exc())


def create_app() -> FastAPI:
    """
    Creates an instance of the FastAPI application.

    Returns:
        An instance of FastAPI with configured routes and lifespan.
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
