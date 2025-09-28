import logging
from typing import Optional

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from config import settings
from app.handlers import UserHandlers, AdminHandlers, SystemHandlers
from app.services import UserService
from app.models import UserRole


class BotManager:
    """
    Class to manage the Telegram bot and its dispatcher.
    """
    def __init__(self):
        self._bot: Optional[Bot] = None
        self._dispatcher: Optional[Dispatcher] = None
        self.user_service = UserService()
        self.creator_id = settings.telegram.creator_id

    def create_bot(self) -> Bot:
        """
        Creates and returns an instance of the bot.

        :return: Bot: Bot instance
        """
        if self.bot is None:
            self._bot = Bot(
                token=settings.telegram.bot_token,
                default=DefaultBotProperties(parse_mode='HTML')
            )
            logging.info('Bot instance created successfully.')

        return self._bot

    def create_dispatcher(self) -> Dispatcher:
        """
        Creates and returns an instance of the dispatcher.

        :return: Dispatcher: Dispatcher instance
        """
        if self._dispatcher is None:
            self._dispatcher = Dispatcher()

            user_handlers = UserHandlers()
            admin_handlers = AdminHandlers()
            system_handlers = SystemHandlers()

            self._dispatcher.include_router(user_handlers.router)
            self._dispatcher.include_router(admin_handlers.router)
            self._dispatcher.include_router(system_handlers.router)

            logging.info('Dispatcher created and handlers registered successfully.')

        return self._dispatcher
    
    async def ensure_creator_exists(self) -> None:
        """
        Creates the creator user if not already present in the database.

        :return: None
        """
        creator = await self.user_service.get_user_by_telegram_id(self.creator_id)
        if creator is None:
            creator = await self.user_service.create_user(
                telegram_id=self.creator_id,
                callsign='creator',
                role=UserRole.CREATOR
            )
            logging.info(f'User with "CREATOR" role created: {creator.callsign.capitalize()}')
        else:
            logging.info('Creator user already exists, skipping creation.')

    @property
    def bot(self) -> Optional[Bot]:
        """
        Returns the bot instance.

        :return: Bot: Bot instance
        """
        return self._bot

    @property
    def dispatcher(self) -> Optional[Dispatcher]:
        """
        Returns the dispatcher instance.

        :return: Dispatcher: Dispatcher instance
        """
        return self._dispatcher

    async def start_polling(self) -> None:
        """
        Starts the bot in polling mode.

        :return: None
        """
        bot = self.create_bot()
        dp = self.create_dispatcher()
        try:
            logging.info('Starting bot in polling mode...')
            await dp.start_polling(bot)
        except Exception as e:
            logging.error(f"Error occurred while starting polling: {e}")
            raise
