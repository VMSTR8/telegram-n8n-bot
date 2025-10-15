import logging
from asyncio import run
import sys

import uvicorn

from app.bot_telegram import (
    BotManager,
    setup_logging
)
from app.bot_telegram import init_database


async def main() -> None:
    """
    Asynchronous main function to initialize the bot, database,

    Returns:
        None
    """
    setup_logging()

    logging.info('Starting application in development mode...')

    bot: BotManager = BotManager()

    await init_database()
    logging.info('Database initialized successfully.')

    await bot.ensure_creator_exists()

    await bot.start_polling()


def run_webhook_mode() -> None:
    """
    Function to run the application in webhook mode using Uvicorn.

    Returns:
        None
    """
    setup_logging()
    logging.info('Starting application in webhook mode...')

    uvicorn.run(
        app='app.api_fastapi:telegrambot_app',
        host='0.0.0.0',
        port=8000,
        reload=False,
        log_level='info'
    )


def run_polling_mode() -> None:
    """
    Function to run the bot in polling mode.

    Returns:
        None
    """
    try:
        run(main())
    except Exception as e:
        logging.error(f'Error occurred while starting the bot: {e}')
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'webhook':
        run_webhook_mode()
    else:
        run_polling_mode()
