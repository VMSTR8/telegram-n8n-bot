import logging
from tortoise import Tortoise
from config import settings
import sys


async def init_database() -> None:
    """
    Initializes the database connection using Tortoise ORM.

    Raises:
        SystemExit: If there is an error during initialization.

    Returns:
        None
    """
    try:
        await Tortoise.init(
            db_url=settings.database.url,
            modules={'models': ['app.models']}
        )
        await Tortoise.get_connection("default").execute_query("SELECT 1;")
        logging.info('Database connection check successful.')

    except Exception as e:
        logging.error(f'Error occurred during database initialization: {e}')
        sys.exit(1)


async def close_database() -> None:
    """
    Closes the database connections.

    Raises:
        Exception: If there is an error while closing connections.
    
    Returns:
        None
    """
    try:
        await Tortoise.close_connections()
        logging.info('Database connections closed successfully.')
    except Exception as e:
        logging.error(f'Error occurred while closing database connections: {e}')
        raise
