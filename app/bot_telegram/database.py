import logging
from tortoise import Tortoise
from config import settings


async def init_database() -> None:
    """
    Инициализация подключения к базе данных с использованием Tortoise ORM.
    :return: None
    """
    try:
        await Tortoise.init(
            db_url=settings.database.url,
            modules={'models': ['app.models']}
        )
        logging.info("Подключение к базе данных успешно инициализировано.")
        logging.warning('ВНИМАНИЕ! Миграции выполняются вручную через aerich!')
        logging.warning('Для справки по миграциям введите команду make help')

    except Exception as e:
        logging.error(f"Ошибка при инициализации базы данных: {e}")
        raise


async def close_database() -> None:
    """
    Закрытие подключений к базе данных.
    :return: None
    """
    try:
        await Tortoise.close_connections()
        logging.info("Подключения к базе данных успешно закрыты.")
    except Exception as e:
        logging.error(f"Ошибка при закрытии подключений к базе данных: {e}")
        raise
