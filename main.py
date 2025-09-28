import logging
from asyncio import run
import sys

from app.bot_telegram import (
    BotManager,
    setup_logging
)
from app.bot_telegram import init_database


async def async_main() -> None:
    """
    Asynchronous main function to initialize and start the bot.

    :return: None
    """
    setup_logging()

    logging.info('Starting application in development mode...')

    bot = BotManager()

    await init_database()
    logging.info('Database initialized successfully.')

    await bot.ensure_creator_exists()

    await bot.start_polling()


def main() -> None:
    """
    Main function to run the asynchronous 
    main function with error handling.

    :return: None
    """
    try:
        run(async_main())
    except Exception as e:
        logging.error(f'Error occurred while starting the bot: {e}')
        sys.exit(1)


if __name__ == "__main__":
    main()
