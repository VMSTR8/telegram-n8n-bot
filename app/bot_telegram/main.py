import logging
from typing import Optional

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from config import settings
from app.handlers import UserHandlers, AdminHandlers
from app.services import UserService
from app.models import UserRole


class BotManager:
    """
    Класс для управления ботом и диспетчером
    """
    def __init__(self):
        self._bot: Optional[Bot] = None
        self._dispatcher: Optional[Dispatcher] = None
        self.user_service = UserService()
        self.creator_id = settings.telegram.creator_id

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
            admin_handlers = AdminHandlers()

            self._dispatcher.include_router(user_handlers.router)
            self._dispatcher.include_router(admin_handlers.router)

            logging.info('Диспетчер создан и обработчики зарегистрированы')

        return self._dispatcher
    
    async def ensure_creator_exists(self) -> None:
        """
        Проверяет и создает пользователя-создателя, если его нет

        :return: None
        """
        creator = await self.user_service.get_user_by_telegram_id(self.creator_id)
        if creator is None:
            creator = await self.user_service.create_user(
                telegram_id=self.creator_id,
                callsign='creator',
                role=UserRole.CREATOR
            )
            logging.info(f'Создан пользователь-создатель: {creator.callsign.capitalize()}')
        else:
            logging.info('Пользователь-создатель уже существует, пропускаем создание')

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
