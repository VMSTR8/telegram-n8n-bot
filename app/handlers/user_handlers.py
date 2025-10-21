import logging
import traceback
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from app.decorators import AuthDecorators as Auth
from app.decorators import CallsignDecorators as Callsign
from app.models import User, Survey
from app.services import UserService, ChatService, SurveyService, MessageQueueService
from config.settings import settings

logger = logging.getLogger(__name__)


class UserHandlers:
    """
    Class to handle user-related commands and interactions.

    Attributes:
        router (Router): The router to register handlers.
        user_service (UserService): Service for user-related operations.
        chat_service (ChatService): Service for chat-related operations.
        survey_service (SurveyService): Service for survey-related operations.
        message_queue_service (MessageQueueService): Service for sending messages.
        tz (timezone): Timezone information from settings.
        _datetime_format (str): Format string for displaying dates and times.
    
    Methods:
        _register_handlers(): Registers command handlers in the router.
        start_command(message): Handles the /start command.
        help_command(message): Handles the /help command.
        register_command(message, callsign): Handles the /reg command for user registration.
        update_command(message): Handles the /update command for updating user profile.
        profile_command(message): Handles the /profile command to show user profile.
        surveys_command(message): Handles the /surveys command to list active surveys.
    """

    def __init__(self):
        self.router: Router = Router()
        self.user_service: UserService = UserService()
        self.chat_service: ChatService = ChatService()
        self.survey_service: SurveyService = SurveyService()
        self.message_queue_service: MessageQueueService = MessageQueueService()
        self.tz: ZoneInfo = settings.timezone_zoneinfo
        self._datetime_format: str = '%d.%m.%Y %H:%M'
        self._register_handlers()

    def _register_handlers(self) -> None:
        """
        Registers command handlers in the router.

        Returns:
            None
        """
        self.router.message(CommandStart())(self.start_command)
        self.router.message(Command('help'))(self.help_command)
        self.router.message(Command('reg'))(self.register_command)
        self.router.message(Command('update'))(self.update_command)
        self.router.message(Command('profile'))(self.profile_command)
        self.router.message(Command('surveys'))(self.surveys_command)

    async def start_command(self, message: Message) -> None:
        """
        Command handler for /start. Sends a welcome message and instructions.

        Args:
            message (Message): Incoming message from the user.
        
        Returns:
            None
        """
        start_text: str = (
            '🚀 _"Стартуем!"_\n\n'
            '👋 Добро пожаловать в бот управления опросами!\n\n'
            'Для начала работы зарегистрируйтесь командой:\n'
            '`/reg позывной`\n\n'
            'Требования к позывному:\n'
            '🔤 Только латинские буквы\n'
            '📏 Длина от 1 до 20 символов\n'
            '🚫 Без цифр, спец символов и пробелов\n'
            '🆔 Позывной должен быть уникальным'
        )
        await self.message_queue_service.send_message(
            chat_id=message.chat.id,
            text=start_text,
            parse_mode='Markdown'
        )

    async def help_command(self, message: Message) -> None:
        """
        Command handler for /help. Sends a list of available commands.

        Args:
            message (Message): Incoming message from the user.

        Returns:
            None
        """
        help_text: str = (
            '📋 Доступные команды:\n\n'
            '👤 Пользователь:\n'
            '• `/reg позывной` - Регистрация в системе\n'
            '• `/update позывной` - Обновить позывной или данные профиля\n'
            '• `/profile` - Посмотреть информацию о себе\n'
            '• `/surveys` - Список активных опросов\n'
            '• `/help` - Показать эту справку\n\n'
            '🔧 Администратор:\n'
            '• `/reserve позывной` - Повесить или снять бронь на прохождение опросов '
            'для конкретного пользователя\n'
            '• `/create_survey название + YYYY-MM-DD HH:MM` - Создать опрос\n'
            '• `/bind_chat` - Привязать чат к боту\n'
            '• `/bind_thread` - Назначить топик для оповещений по опросам\n'
            '• `/unbind_thread` - Отвязать топик для оповещений по опросам\n'
            '• `/admin_list` - Показать список администраторов\n\n'
            '👑 Создатель:\n'
            '• `/unbind_chat` - Отвязать чат от бота\n'
            '• `/add_admin позывной` - Добавить администратора\n'
            '• `/remove_admin позывной` - Убрать администратора'
        )

        await self.message_queue_service.send_message(
            chat_id=message.chat.id,
            text=help_text,
            parse_mode='Markdown',
            message_id=message.message_id
        )

    @Auth.required_not_private_chat
    @Auth.required_chat_bind
    @Callsign.validate_callsign_create
    async def register_command(self, message: Message, callsign: str) -> None:
        """
        Command handler for /reg. Registers a new user with the provided callsign.

        Args:
            message (Message): Incoming message from the user.
            callsign (str): The callsign provided by the user for registration.
        
        Returns:
            None
        """
        try:
            user_exists: User | None = await self.user_service.get_user_by_telegram_id(message.from_user.id)
            if user_exists:
                await self.message_queue_service.send_message(
                    chat_id=message.chat.id,
                    text=f'❌ Вы уже зарегистрированы в системе.\n\n'
                         f'Ваш позывной: *{user_exists.callsign.capitalize()}*',
                    parse_mode='Markdown',
                    message_id=message.message_id
                )
                return

            user: User = await self.user_service.create_user(
                telegram_id=message.from_user.id,
                callsign=callsign.lower(),
                first_name=(message.from_user.first_name.lower()
                            if message.from_user.first_name else None),
                last_name=(message.from_user.last_name.lower()
                           if message.from_user.last_name else None),
                username=(message.from_user.username.lower()
                          if message.from_user.username else None)
            )

            await self.message_queue_service.send_message(
                chat_id=message.chat.id,
                text=f'✅ Вы успешно зарегистрировались!\n'
                     f'Позывной: {user.callsign.capitalize()}\n'
                     f'Имя: {user.first_name.capitalize() if user.first_name else 'Не указано'}\n'
                     f'Фамилия: {user.last_name.capitalize() if user.last_name else 'Не указана'}\n'
                     f'Username: {f'@{user.username.replace('_', r'\_')}' if user.username else 'Username не указан'}',
                parse_mode='Markdown',
                message_id=message.message_id
            )

        except ValueError as ve:
            await self.message_queue_service.send_message(
                chat_id=message.chat.id,
                text=f'❌ Ошибка регистрации: {ve}',
                parse_mode='Markdown',
                message_id=message.message_id
            )
        except Exception as e:
            logger.error('Error occurred during registration: %s\n%s', e, traceback.format_exc())
            await self.message_queue_service.send_message(
                chat_id=message.chat.id,
                text='❌ Произошла ошибка при регистрации. Пожалуйста, попробуйте позже.',
                parse_mode='Markdown',
                message_id=message.message_id
            )

    @Auth.required_user_registration
    @Callsign.validate_callsign_update
    async def update_command(self, message: Message) -> None:
        """
        Command handler for /update. Updates the user's profile information.
        If a callsign is provided, updates it as well.

        Args:
            message (Message): Incoming message from the user.

        Returns:
            None
        """
        try:
            data: dict[str, str | datetime | None] = {}

            user: User = await self.user_service.get_user_by_telegram_id(message.from_user.id)

            data['first_name'] = (message.from_user.first_name.lower()
                                  if message.from_user.first_name else None)
            data['last_name'] = (message.from_user.last_name.lower()
                                 if message.from_user.last_name else None)
            data['username'] = (message.from_user.username.lower()
                                if message.from_user.username else None)
            data['updated_at'] = datetime.now(tz=self.tz)

            args: list[str] = message.text.split()

            if len(args) >= 2:
                data['callsign'] = args[1].lower()

            await self.user_service.update_user(user.telegram_id, **data)

            await self.message_queue_service.send_message(
                chat_id=message.chat.id,
                text='✅ Профиль успешно обновлён!',
                parse_mode='Markdown',
                message_id=message.message_id
            )

        except ValueError as ve:
            await self.message_queue_service.send_message(
                chat_id=message.chat.id,
                text=f'❌ Ошибка обновления профиля: {ve}',
                parse_mode='Markdown',
                message_id=message.message_id
            )
        except Exception as e:
            logger.error('Error occurred while updating user profile: %s\n%s', e, traceback.format_exc())
            await self.message_queue_service.send_message(
                chat_id=message.chat.id,
                text='❌ Произошла ошибка при обновлении профиля. Пожалуйста, попробуйте позже.',
                parse_mode='Markdown',
                message_id=message.message_id
            )

    @Auth.required_user_registration
    async def profile_command(self, message: Message) -> None:
        """
        Command handler for /profile. Sends user profile information.

        Args:
            message (Message): Incoming message from the user.
        
        Returns:
            None
        """
        user: User = await self.user_service.get_user_by_telegram_id(message.from_user.id)

        profile_text: str = (
            f'👤 *Профиль пользователя*\n\n'
            f'🆔 Позывной: `{user.callsign.capitalize()}`\n'
            f'👤 Имя: {user.first_name.capitalize() if user.first_name else 'Не указано'}\n'
            f'👥 Фамилия: {user.last_name.capitalize() if user.last_name else 'Не указана'}\n'
            f'🔗 Username: {f'@{user.username.replace('_', r'\_')}' if user.username else 'Не указан'}\n'
            f'📅 Зарегистрирован: '
            f'{user.created_at.astimezone(tz=self.tz).strftime(self._datetime_format)}\n'
            f'🔄 Профиль обновлён: '
            f'{user.updated_at.astimezone(tz=self.tz).strftime(self._datetime_format)}\n'
            f'🛡️ Бронь от опросов: {'Есть' if user.reserved else 'Нет'}\n'
            f'⚙️ Роль: {user.role.value.capitalize()}'
        )

        await self.message_queue_service.send_message(
            chat_id=message.chat.id,
            text=profile_text,
            parse_mode='Markdown',
            message_id=message.message_id
        )

    @Auth.required_chat_bind
    @Auth.required_user_registration
    async def surveys_command(self, message: Message) -> None:
        """
        Command handler for /surveys. Sends a list of active surveys.

        :param message: Message - incoming message from the user
        :return: None
        """
        active_surveys: list[Survey] | None = await self.survey_service.get_active_surveys()

        if not active_surveys:
            await self.message_queue_service.send_message(
                chat_id=message.chat.id,
                text='В данный момент нет активных опросов.',
                parse_mode='Markdown',
                message_id=message.message_id
            )
            return

        surveys_text: str = '📋 *Активные опросы:*\n\n'
        for survey in active_surveys:
            surveys_text += (
                f'• *{survey.title}*\n'
                f'  🔗 [Перейти к опросу]({survey.form_url})\n'
                f'  🕒 Завершение: {survey.ended_at.astimezone(
                    tz=self.tz
                ).strftime(self._datetime_format)}\n\n'
            )

        await self.message_queue_service.send_message(
            chat_id=message.chat.id,
            text=surveys_text,
            parse_mode='Markdown',
            disable_web_page_preview=True,
            message_id=message.message_id
        )
