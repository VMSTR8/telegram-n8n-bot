import logging

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, CommandStart

from app.services import UserService, ChatService, SurveyService
from app.decorators import validate_callsign_create, required_user_registration, required_chat_bind


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
            '• `/bind` - Привязать чат к бота\n'
            '• `/unbind` - Отвязать чат от бота\n'
            '• `/bind_thread` - Назначить тред для оповещений по опросам\n'
            '• `/unbind_thread` - Снять тред для оповещений по опросам\n'
            '• `/reserve позывной` - Повесить или снять бронь на прохождение опросов '
            'для конкретного пользователя\n\n'
            '👑 Создатель:\n'
            '• `/add_admin позывной` - Добавить администратора\n'
            '• `/remove_admin позывной` - Убрать администратора\n'
            '• `/admin_list` - Показать список администраторов\n'
            '• `/create_survey название время_окончания` - Создать опрос\n'
        )
        await message.reply(text=help_text, parse_mode='Markdown')

    @validate_callsign_create
    async def register_command(self, message: Message, callsign: str) -> None:
        """
        Обработчик команды /reg. Регистрирует нового пользователя с указанным позывным.

        :param message: Message - входящее сообщение от пользователя
        :param callsign: str - позывной пользователя
        :return: None
        """
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

    @required_user_registration
    async def update_command(self, message: Message) -> None:
        # TODO: Реализовать обновление профиля пользователя
        pass

    @required_user_registration
    async def profile_command(self, message: Message) -> None:
        """
        Обработчик команды /profile. Отправляет информацию о профиле пользователя.

        :param message: Message - входящее сообщение от пользователя
        :return: None
        """
        user = await self.user_service.get_user_by_telegram_id(message.from_user.id)

        profile_text = (
            f'👤 *Профиль пользователя*\n\n'
            f'🆔 Позывной: `{user.callsign}'
            f'👤 Имя: {user.first_name.capitalize() if user.first_name else 'Не указано'}\n'
            f'👥 Фамилия: {user.last_name.capitalize() if user.last_name else 'Не указана'}\n'
            f'🔗 Username: {f'@{user.username}' if user.username else 'username не указан'}\n'
            f'📅 Зарегистрирован: {user.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n'
            f'🔄 Профиль обновлён: {user.updated_at.strftime('%Y-%m-%d %H:%M:%S')}\n'
            f'🛡️ Бронь от опросов: {'Есть' if user.reserved else 'Нет'}\n'
            f'⚙️ Роль: {user.role.value.capitalize()}'
        )

        await message.reply(text=profile_text, parse_mode='Markdown')

    @required_chat_bind
    @required_user_registration
    async def surveys_command(self, message: Message) -> None:
        """
        Обработчик команды /surveys. Отправляет список активных опросов
        с прикрепленными ссылками.

        :param message: Message - входящее сообщение от пользователя
        :return: None
        """
        active_surveys = await self.survey_service.get_active_surveys()

        if not active_surveys:
            await message.reply(
                text='В данный момент нет активных опросов\n¯\_(ツ)_/¯',
                parse_mode='Markdown'
            )
            return

        surveys_text = '📋 *Активные опросы:*\n\n'
        for survey in active_surveys:
            surveys_text += (
                f'• *{survey.title}*\n'
                f'  🔗 [Перейти к опросу]({survey.form_url})\n'
                f'  🕒 Завершение: {survey.ended_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n'
            )

        await message.reply(text=surveys_text, parse_mode='Markdown')
