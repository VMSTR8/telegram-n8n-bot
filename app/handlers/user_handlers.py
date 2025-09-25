import logging

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, CommandStart

from app.services import UserService, ChatService, SurveyService
from app.decorators import validate_callsign_create


class UserHandlers:
    """
    Класс для обработки пользовательских команд и сообщений.
    """
    def __init__(self):
        self.router = Router()
        self.user_service = UserService()
        self.chat_service = ChatService()
        self.survey_service = SurveyService()
        self._register_handlers()

    def _register_handlers(self) -> None:
        """
        Регистрирует обработчики команд в роутере.

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
        Обработчик команды /start. Отправляет приветственное сообщение и инструкции по регистрации.

        :param message: Message - входящее сообщение от пользователя
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
        Обработчик команды /help. Отправляет список доступных команд и их описание.

        :param message: Message - входящее сообщение от пользователя
        :return: None
        """
        help_text = (
            '📋 Доступные команды:\n\n'
            '👤 Пользователь:\n'
            '• `/reg позывной` - Регистрация в системе\n'
            '• `/update позывной` - Обновить позывной или данные профиля\n'
            '• `/profile` - Информация о профиле\n'
            '• `/surveys` - Статус прохождения опросов\n'
            '• `/help` - Показать эту справку\n\n'
            '🔧 Администратор:\n'
            '👑 Создатель:\n'
        )
        await message.reply(text=help_text, parse_mode='Markdown')

    @validate_callsign_create
    async def register_command(self, message: Message, callsign: str) -> None:
        try:
            user_exists = await self.user_service.get_user_by_telegram_id(message.from_user.id)
            if user_exists:
                await message.reply(
                    text=f'❌ Вы уже зарегистрированы в системе.\n'
                    f'Ваш позывной: {user_exists.callsign.capitalize()}\n',
                    parse_mode='Markdown'
                )
                return

            user = await self.user_service.create_user(
                telegram_id=message.from_user.id,
                callsign=callsign.lower(),
                first_name=message.from_user.first_name.lower(),
                last_name=message.from_user.last_name.lower(),
                username=message.from_user.username.lower()
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
            logging.error(f'Ошибка при регистрации пользователя: {e}')

    async def update_command(self, message: Message) -> None:
        pass

    async def profile_command(self, message: Message) -> None:
        pass

    async def surveys_command(self, message: Message) -> None:
        pass
