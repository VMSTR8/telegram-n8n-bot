import logging
from datetime import datetime

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, CommandStart

from app.services import UserService, ChatService, SurveyService
from app.decorators import CallsignDecorators as Callsign
from app.decorators import AuthDecorators as Auth
from config.settings import settings


class UserHandlers:
    """
    Class to handle user-related commands and interactions.
    """

    def __init__(self):
        self.router = Router()
        self.user_service = UserService()
        self.chat_service = ChatService()
        self.survey_service = SurveyService()
        self.tz = settings.timezone_zoneinfo
        self._datetime_format = '%d.%m.%Y %H:%M'
        self._register_handlers()

    def _register_handlers(self) -> None:
        """
        Registers command handlers in the router.

        :return: None
        """
        self.router.message(CommandStart())(self.start_command)
        self.router.message(Command('help'))(self.help_command)
        self.router.message(Command('reg'))(self.register_command)
        self.router.message(Command('update'))(self.update_command)
        self.router.message(Command('profile'))(self.profile_command)
        self.router.message(Command('surveys'))(self.surveys_command)

    @staticmethod
    async def start_command(message: Message) -> None:
        """
        Command handler for /start. Sends a welcome message and instructions.

        :param message: Message - incoming message from the user
        :return: None
        """
        start_text = (
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

        await message.answer(text=start_text, parse_mode='Markdown')

    @staticmethod
    async def help_command(message: Message) -> None:
        """
        Command handler for /help. Sends a list of available commands.

        :param message: Message - incoming message from the user
        :return: None
        """
        help_text = (
            '📋 Доступные команды:\n\n'
            '👤 Пользователь:\n'
            '• `/reg позывной` - Регистрация в системе\n'
            '• `/update позывной` - Обновить позывной или данные профиля\n'
            '• `/profile` - Посмотреть информацию о себе\n'
            '• `/surveys` - Список активных опросов\n'
            '• `/help` - Показать эту справку\n\n'
            '🔧 Администратор:\n'
            '• `/bind_chat` - Привязать чат к боту\n'
            '• `/bind_thread` - Назначить топик для оповещений по опросам\n'
            '• `/unbind_thread` - Отвязать топик для оповещений по опросам\n'
            '• `/reserve позывной` - Повесить или снять бронь на прохождение опросов '
            'для конкретного пользователя\n'
            '• `/create_survey название дата_окончания` - Создать опрос\n'
            '• `/admin_list` - Показать список администраторов\n\n'
            '👑 Создатель:\n'
            '• `/unbind_chat` - Отвязать чат от бота\n'
            '• `/add_admin позывной` - Добавить администратора\n'
            '• `/remove_admin позывной` - Убрать администратора'
        )
        await message.reply(text=help_text, parse_mode='Markdown')

    @Callsign.validate_callsign_create
    async def register_command(self, message: Message, callsign: str) -> None:
        """
        Command handler for /reg. Registers a new user with the provided callsign.

        :param message: Message - incoming message from the user
        :param callsign: str - user's callsign
        :return: None
        """
        try:
            user_exists = await self.user_service.get_user_by_telegram_id(message.from_user.id)
            if user_exists:
                await message.reply(
                    text=f'❌ Вы уже зарегистрированы в системе.\n\n'
                    f'Ваш позывной: *{user_exists.callsign.capitalize()}*',
                    parse_mode='Markdown'
                )
                return

            user = await self.user_service.create_user(
                telegram_id=message.from_user.id,
                callsign=callsign.lower(),
                first_name=(message.from_user.first_name.lower()
                            if message.from_user.first_name else None),
                last_name=(message.from_user.last_name.lower()
                           if message.from_user.last_name else None),
                username=(message.from_user.username.lower()
                          if message.from_user.username else None)
            )

            await message.reply(
                text=f'✅ Вы успешно зарегистрировались!\n'
                f'Позывной: {user.callsign.capitalize()}\n'
                f'Имя: {user.first_name.capitalize() if user.first_name else 'Не указано'}\n'
                f'Фамилия: {user.last_name.capitalize() if user.last_name else 'Не указана'}\n'
                f'Username: {f'@{user.username}' if user.username else 'username не указан'}',
                parse_mode='Markdown'
            )

        except ValueError as e:
            await message.reply(f'❌ Ошибка регистрации: {e}')
        except Exception as e:
            await message.reply(
                '❌ Произошла ошибка при регистрации. Пожалуйста, попробуйте позже.'
            )
            logging.error(f'Error occurred during registration: {e}')

    @Auth.required_user_registration
    @Callsign.validate_callsign_update
    async def update_command(self, message: Message) -> None:
        """
        Command handler for /update. Updates the user's profile information.
        If a callsign is provided, updates it as well.

        :param message: Message - incoming message from the user
        :return: None
        """
        try:
            data = {}

            user = await self.user_service.get_user_by_telegram_id(message.from_user.id)

            data['first_name'] = (message.from_user.first_name.lower()
                                  if message.from_user.first_name else None)
            data['last_name'] = (message.from_user.last_name.lower()
                                 if message.from_user.last_name else None)
            data['username'] = (message.from_user.username.lower()
                                if message.from_user.username else None)
            data['updated_at'] = datetime.now(tz=self.tz)

            args = message.text.split()

            if len(args) >= 2:
                data['callsign'] = args[1].lower()

            await self.user_service.update_user(user.telegram_id, **data)

            await message.reply('✅ Профиль успешно обновлён!')

        except ValueError as e:
            await message.reply(f'❌ Ошибка обновления профиля: {e}')
        except Exception as e:
            await message.reply(
                '❌ Произошла ошибка при обновлении профиля. Пожалуйста, попробуйте позже.'
            )
            logging.error(f'Error occurred while updating user profile: {e}')

    @Auth.required_user_registration
    async def profile_command(self, message: Message) -> None:
        """
        Command handler for /profile. Sends user profile information.

        :param message: Message - incoming message from the user
        :return: None
        """
        user = await self.user_service.get_user_by_telegram_id(message.from_user.id)

        profile_text = (
            f'👤 *Профиль пользователя*\n\n'
            f'🆔 Позывной: `{user.callsign.capitalize()}`\n'
            f'👤 Имя: {user.first_name.capitalize() if user.first_name else 'Не указано'}\n'
            f'👥 Фамилия: {user.last_name.capitalize() if user.last_name else 'Не указана'}\n'
            f'🔗 Username: {f'@{user.username}' if user.username else 'Не указан'}\n'
            f'📅 Зарегистрирован: '
            f'{user.created_at.astimezone(tz=self.tz).strftime(self._datetime_format)}\n'
            f'🔄 Профиль обновлён: '
            f'{user.updated_at.astimezone(tz=self.tz).strftime(self._datetime_format)}\n'
            f'🛡️ Бронь от опросов: {'Есть' if user.reserved else 'Нет'}\n'
            f'⚙️ Роль: {user.role.value.capitalize()}'
        )

        await message.reply(text=profile_text, parse_mode='Markdown')

    @Auth.required_chat_bind
    @Auth.required_user_registration
    async def surveys_command(self, message: Message) -> None:
        """
        Command handler for /surveys. Sends a list of active surveys.

        :param message: Message - incoming message from the user
        :return: None
        """
        active_surveys = await self.survey_service.get_active_surveys()

        if not active_surveys:
            await message.reply(
                text='В данный момент нет активных опросов.',
                parse_mode='Markdown'
            )
            return

        surveys_text = '📋 *Активные опросы:*\n\n'
        for survey in active_surveys:
            surveys_text += (
                f'• *{survey.title}*\n'
                f'  🔗 [Перейти к опросу]({survey.form_url})\n'
                f'  🕒 Завершение: {survey.ended_at.astimezone(
                    tz=self.tz
                ).strftime(self._datetime_format)}\n\n'
            )

        await message.reply(text=surveys_text, parse_mode='Markdown')
