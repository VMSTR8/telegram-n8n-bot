import logging
from typing import Optional

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from config import settings


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

            # TODO: Добавить обработчики

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

    async def start_webhook(self) -> None:
        """
        Запускает бота в режиме webhook
        :return: None
        """
        if not settings.telegram.webhook_url or not settings.telegram.webhook_secret:
            raise ValueError("Webhook URL и секретный ключ должны быть заданы для режима webhook")

        bot = self.create_bot()
        webhook_url = f'{settings.telegram.webhook_url}/telegram_webhook'
        try:
            await bot.set_webhook(
                url=webhook_url,
                secret_token=settings.telegram.webhook_secret
            )
            logging.info('Бот запущен в режиме webhook')
        except Exception as e:
            logging.error(f"Ошибка установки webhook: {e}")
            raise
