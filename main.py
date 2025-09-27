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
    Асинхронная основная функция для инициализации и запуска бота.

    :return: None
    """
    setup_logging()
    
    logging.info('Запуск приложения в режиме development...')

    bot = BotManager()
    
    await init_database()
    logging.info('База данных инициализирована')
    
    await bot.ensure_creator_exists()

    await bot.start_polling()

def main() -> None:
    """
    Так! Это все пока пишется и разрабатывается.
    Когда апишку напишу, то и тут нормальный main сделаю.
    Нечего тут смотреть и читать докстринг этот.
    Кыш отседа.
    Иди свой проект делай.
    Ну или не делай. Можешь и тут посидеть.
    Зачем я пишу это все?
    Да просто так.
    Лишь бы мне не писать код. Ты же тоже тут,
    потому что не хочешь писать код, а хочешь читать докстринги.
    Вот и я так же.
    Пойдем лучше код писать. (или нет)
    """
    try:
        run(async_main())
    except Exception as e:
        logging.error(f'Ошибка при запуске бота: {e}')
        sys.exit(1)


if __name__ == "__main__":
    main()
