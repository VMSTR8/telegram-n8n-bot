import logging
from asyncio import run
from app.bot_telegram.bot import BotManager
from app.bot_telegram.logging import setup_logging


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
    setup_logging()
    logging.info('Бот запускается в development режиме...')

    bot = BotManager()

    run(bot.start_polling())


if __name__ == "__main__":
    main()
