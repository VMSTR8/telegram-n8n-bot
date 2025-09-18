import sys
from loguru import logger


def setup_logging() -> None:
    """
    Настройка логирования с использованием Loguru.
    """
    logger.remove()

    # Логирование в консоль
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
               "<level>{message}</level>",
        level="INFO",
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # Логирование в файл
    logger.add(
        'logs/telegram_bot.log',
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="1 day",
        retention="30 days",
        compression="zip",
    )

    # Логирование ошибок в отдельный файл
    logger.add(
        'logs/telegram_bot_error.log',
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="1 week",
        retention="90 days",
        compression="zip",
    )

    logger.info("Логирование настроено.")
