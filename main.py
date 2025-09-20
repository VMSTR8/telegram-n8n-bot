from asyncio import run
from app.bot_telegram.bot import BotManager
from app.bot_telegram.logging import setup_logging

# ТЕСТОВЫЙ ЗАПУСК БОТА
if __name__ == "__main__":
    setup_logging()
    start = BotManager()
    run(start.start_polling())
