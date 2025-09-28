from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from app.services import UserService, ChatService, SurveyService
from app.decorators import AuthDecorators as Auth
from config.settings import settings


class AdminHandlers:
    """
    Класс для обработки административных команд и сообщений.
    """

    def __init__(self):
        self.router = Router()
        self.user_service = UserService()
        self.chat_service = ChatService()
        self.survey_service = SurveyService()
        self.tz = settings.timezone_zoneinfo
        self._register_handlers()

    def _register_handlers(self) -> None:

        # Команды для администраторов
        self.router.message(Command('reserve'))(self.reserve_user_command)
        self.router.message(Command('create_survey'))(self.create_survey_command)

        # Команды для создателя
        self.router.message(Command('bind_chat'))(self.bind_chat_command)
        self.router.message(Command('unbind_chat'))(self.unbind_chat_command)
        self.router.message(Command('bind_thread'))(self.bind_thread_command)
        self.router.message(Command('unbind_thread'))(self.unbind_thread_command)
        self.router.message(Command('add_admin'))(self.add_admin_command)
        self.router.message(Command('remove_admin'))(self.remove_admin_command)
        self.router.message(Command('admin_list'))(self.admin_list_command)

    @Auth.required_admin
    async def reserve_user_command(self, message: Message) -> None:
        """
        Переключает статус брони пользователя от опросов по его позывному.

        :param message: Message - входящее сообщение от пользователя
        :return: None
        """
        args = message.text.split(maxsplit=1)
        if len(args) < 2 or not args[1].strip():
            await message.reply(
                text='❌ Пожалуйста, укажите позывной пользователя после команды.\n'
                     'Пример: `/reserve позывной`',
                parse_mode='Markdown'
            )
            return

        callsign = args[1].strip()
        callsign = callsign.lower()
        
        user = await self.user_service.get_user_by_callsign(callsign=callsign)
        
        if not user:
            await message.reply(
                text=f'❌ Пользователь с позывным `{callsign.capitalize()}` не найден.',
                parse_mode='Markdown'
            )
            return

        user.reserved = not user.reserved
        await user.save()
        await message.reply(
            text=f'✅ Статус брони от опросов пользователя `{callsign.capitalize()}` изменён на: '
                 f'{"Есть" if user.reserved else "Нет"}.',
            parse_mode='Markdown'
        )

    @Auth.required_admin
    async def create_survey_command(self, message: Message) -> None:
        pass

    @Auth.required_creator
    @Auth.required_not_private_chat
    async def bind_chat_command(self, message: Message) -> None:
        """
        Привязывает чат к базе данных: если чат уже существует в базе, обновляет его Telegram ID, 
        если нет — создает новую запись для чата.

        :param message: Сообщение с командой
        :return: None
        """
        chat_exists = await self.chat_service.get_chat_by_telegram_id(message.chat.id)

        if chat_exists:
            await message.reply('❌ Этот чат уже привязан к базе данных.')
            return

        await self.chat_service.bind_chat(
            telegram_id=message.chat.id,
            chat_type=message.chat.type,
            title=message.chat.title or 'Без названия'
        )

        await message.reply('✅ Чат успешно привязан к базе данных.')

    @Auth.required_creator
    @Auth.required_not_private_chat
    async def unbind_chat_command(self, message: Message) -> None:
        """
        Отвязывает чат от базы данных: если чат не найден, сообщает об этом, иначе удаляет привязку.
        Если чат уже был отвязан ранее, возвращает сообщение об ошибке.

        :param message: Сообщение с командой
        :return: None
        """
        is_unbound = await self.chat_service.unbind_chat(telegram_id=message.chat.id)
        if is_unbound:
            await message.reply('✅ Чат успешно отвязан от базы данных.')
        else:
            await message.reply('❌ Не удалось отвязать чат.\nВозможно, он уже был отвязан ранее.')

    @Auth.required_creator
    async def bind_thread_command(self, message: Message) -> None:
        pass

    @Auth.required_creator
    async def unbind_thread_command(self, message: Message) -> None:
        pass

    @Auth.required_creator
    async def add_admin_command(self, message: Message) -> None:
        pass

    @Auth.required_creator
    async def remove_admin_command(self, message: Message) -> None:
        pass

    @Auth.required_creator
    async def admin_list_command(self, message: Message) -> None:
        pass
