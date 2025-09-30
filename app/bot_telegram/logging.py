import logging
import logging.handlers
from pathlib import Path


def setup_logging() -> None:
    """
    Sets up logging configuration for the application.
    """
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)

    console_format = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s',
        '%Y-%m-%d %H:%M:%S'
    )
    file_format = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s',
        '%Y-%m-%d %H:%M:%S'
    )

    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Set up console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)

    # Set up file handlers
    file_handler = logging.handlers.TimedRotatingFileHandler(
        logs_dir / 'telegram_bot.log', when='midnight', backupCount=30, encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(file_format)
    root_logger.addHandler(file_handler)

    # Set up error handler
    error_handler = logging.handlers.TimedRotatingFileHandler(
        logs_dir / 'telegram_bot_error.log', when='W0', backupCount=13, encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_format)
    root_logger.addHandler(error_handler)

    # Suppress overly verbose logs from external libraries
    aiogram_events_logger = logging.getLogger('aiogram')
    aiogram_events_logger.setLevel(logging.WARNING)

    logging.info('Logging is set up.')
