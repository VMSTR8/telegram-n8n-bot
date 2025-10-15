import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from config import settings
from app.handlers import UserHandlers, AdminHandlers, SystemHandlers
from app.services import UserService
from app.models import UserRole, User


class BotManager:
    """
    Class to manage the Telegram bot and its dispatcher.

    Attributes:
        bot (Bot): Instance of the Telegram bot.
        dispatcher (Dispatcher): Instance of the bot's dispatcher.
        user_service (UserService): Service for user-related operations.
        creator_id (int): Telegram ID of the bot creator.
    
    Methods:
        create_bot(): Creates and returns an instance of the bot.
        create_dispatcher(): Creates and returns an instance of the dispatcher.
        ensure_creator_exists(): Creates the creator user if not already present in the database.
        start_polling(): Starts the bot in polling mode.
    
    Properties:
        bot: Returns the bot instance.
        dispatcher: Returns the dispatcher instance.
    """
    def __init__(self) -> None:
        self._bot: Bot | None = None
        self._dispatcher: Dispatcher | None = None
        self.user_service: UserService = UserService()
        self.creator_id: int = settings.telegram.creator_id

    def create_bot(self) -> Bot:
        """
        Creates and returns an instance of the bot.

        Raises:
            ValueError: If the bot token is not set in the configuration.

        Returns:
            Bot instance
        """
        if not settings.telegram.bot_token:
            logging.error('Bot token is not set in the configuration.')
            raise ValueError('Bot token is required to create a Bot instance.')

        if self.bot is None:
            self._bot: Bot = Bot(
                token=settings.telegram.bot_token,
                default=DefaultBotProperties(parse_mode='HTML')
            )
            logging.info('Bot instance created successfully.')

        return self._bot

    def create_dispatcher(self) -> Dispatcher:
        """
        Creates and returns an instance of the dispatcher.

        Returns:
            Dispatcher instance
        """
        if self._dispatcher is None:
            self._dispatcher: Dispatcher = Dispatcher()

            user_handlers: UserHandlers = UserHandlers()
            admin_handlers: AdminHandlers = AdminHandlers()
            system_handlers: SystemHandlers = SystemHandlers()

            self._dispatcher.include_router(user_handlers.router)
            self._dispatcher.include_router(admin_handlers.router)
            self._dispatcher.include_router(system_handlers.router)

            logging.info('Dispatcher created and handlers registered successfully.')

        return self._dispatcher
    
    async def ensure_creator_exists(self) -> None:
        """
        Creates the creator user if not already present in the database.

        Returns:
            None
        """
        creator: User | None = await self.user_service.get_user_by_telegram_id(self.creator_id)
        if creator is None:
            creator: User = await self.user_service.create_user(
                telegram_id=self.creator_id,
                callsign='creator',
                role=UserRole.CREATOR
            )
            logging.info(f'User with "CREATOR" role created: {creator.callsign.capitalize()}')
        else:
            logging.info('Creator user already exists, skipping creation.')

    @property
    def bot(self) -> Bot | None:
        """
        Returns the bot instance.

        Returns:
            Bot instance
        """
        return self._bot

    @property
    def dispatcher(self) -> Dispatcher | None:
        """
        Returns the dispatcher instance.

        Returns:
            Dispatcher instance
        """
        return self._dispatcher

    async def start_polling(self) -> None:
        """
        Starts the bot in polling mode.

        Raises:
            Exception: If an error occurs while starting polling.
        
        Returns:
            None
        """
        bot: Bot = self.create_bot()
        dp: Dispatcher = self.create_dispatcher()
        try:
            logging.info('Starting bot in polling mode...')
            await dp.start_polling(bot)
        except Exception as e:
            logging.error(f"Error occurred while starting polling: {e}")
            raise
