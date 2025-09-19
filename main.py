from app.bot_telegram.bot import BotManager
from asyncio import run

# ТЕСТОВЫЙ ЗАПУСК БОТА
if __name__ == "__main__":
    start = BotManager()
    run(start.start_polling())
