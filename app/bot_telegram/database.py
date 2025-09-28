import logging
from tortoise import Tortoise
from config import settings
import sys


async def init_database() -> None:
    """
    Initializes the database connection using Tortoise ORM.

    :return: None
    """
    try:
        await Tortoise.init(
            db_url=settings.database.url,
            modules={'models': ['app.models']}
        )
        await Tortoise.get_connection("default").execute_query("SELECT 1;")
        logging.info("Подключение к базе данных успешно инициализировано.")

    except Exception as e:
        logging.error(f"Ошибка при инициализации базы данных: {e}")
        sys.exit(1)


async def close_database() -> None:
    """
    Closes the database connections
    .
    :return: None
    """
    try:
        await Tortoise.close_connections()
        logging.info("Подключения к базе данных успешно закрыты.")
    except Exception as e:
        logging.error(f"Ошибка при закрытии подключений к базе данных: {e}")
        raise
