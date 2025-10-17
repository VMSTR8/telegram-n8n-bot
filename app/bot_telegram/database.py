import logging
import traceback
from tortoise import Tortoise
from config import settings
import sys

logger = logging.getLogger(__name__)

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
        logger.info('Database connection checked successfully.')

    except Exception as e:
        logger.error('Failed to initialize database: %s\n%s', str(e), traceback.format_exc())
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
        logger.info('Database connections closed successfully.')
    except Exception as e:
        logger.error('Failed to close database connections: %s\n%s', str(e), traceback.format_exc())
        raise
