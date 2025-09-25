import logging
from typing import Optional

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from config import settings
from app.handlers import UserHandlers


class BotManager:
    """
    Класс для управления ботом и диспетчером
    """
    def __init__(self):
        self._bot: Optional[Bot] = None
        self._dispatcher: Optional[Dispatcher] = None

    def create_bot(self) -> Bot:
        """
        Создает и возвращает экземпляр бота

        :return: Bot: Экземпляр бота
        """
        if self.bot is None:
            self._bot = Bot(
                token=settings.telegram.bot_token,
                default=DefaultBotProperties(parse_mode='HTML')
            )
            logging.info('Бот создан')

        return self._bot

    def create_dispatcher(self) -> Dispatcher:
        """
        Создает и возвращает экземпляр диспетчера

        :return: Dispatcher: Экземпляр диспетчера
        """
        if self._dispatcher is None:
            self._dispatcher = Dispatcher()

            user_handlers = UserHandlers()

            self._dispatcher.include_router(user_handlers.router)

            logging.info('Диспетчер создан и обработчики зарегистрированы')

        return self._dispatcher

    @property
    def bot(self) -> Optional[Bot]:
        """
        Возвращает экземпляр бота

        :return: Bot: Экземпляр бота
        """
        return self._bot

    @property
    def dispatcher(self) -> Optional[Dispatcher]:
        """
        Возвращает экземпляр диспетчера

        :return: Dispatcher: Экземпляр диспетчера
        """
        return self._dispatcher

    async def start_polling(self) -> None:
        """
        Запускает бота в режиме polling

        :return: None
        """
        bot = self.create_bot()
        dp = self.create_dispatcher()
        try:
            logging.info('Запуск бота в режиме polling')
            await dp.start_polling(bot)
        except Exception as e:
            logging.error(f"Ошибка запуска polling режима: {e}")
            raise
