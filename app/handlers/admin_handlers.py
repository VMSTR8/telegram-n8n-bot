import json
from datetime import datetime
from types import SimpleNamespace

import aiohttp
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.decorators import AuthDecorators as Auth
from app.decorators import SurveyCreationDecorators as CreateSurvey
from app.models import UserRole, User, Chat, SurveyTemplate
from app.schemas import SurveyData
from app.services import (
    UserService,
    ChatService,
    ChatAlreadyBoundError,
    SurveyService,
    MessageQueueService,
    SurveyTemplateService
)
from config.settings import settings


class AdminHandlers:
    """
    Class to handle admin-related commands and interactions.

    Attributes:
        router (Router): The Aiogram router to register handlers.
        user_service (UserService): Service for user-related operations.
        chat_service (ChatService): Service for chat-related operations.
        survey_service (SurveyService): Service for survey-related operations.
        message_queue_service (MessageQueueService): Service for sending messages.
        survey_template_service (SurveyTemplateService): Service for survey template operations.
        n8n (SimpleNamespace): Configuration for n8n webhook integration.
        tz (str): Timezone information from settings.
    
    Methods:
        _register_handlers(): Registers command handlers in the router.
        reserve_command(message: Message): Handles the /reserve command.
        create_survey_command(message: Message, title: str, ended_at: datetime): Handles the /create_survey command.
        bind_chat_command(message: Message): Handles the /bind_chat command.
        unbind_chat_command(message: Message): Handles the /unbind_chat command.
        bind_thread_command(message: Message): Handles the /bind_thread command.
        unbind_thread_command(message: Message): Handles the /unbind_thread command.
        add_admin_command(message: Message): Handles the /add_admin command.
        remove_admin_command(message: Message): Handles the /remove_admin command.
        admin_list_command(message: Message): Handles the /admin_list command.
    """

    def __init__(self) -> None:
        self.router: Router = Router()
        self.user_service: UserService = UserService()
        self.chat_service: ChatService = ChatService()
        self.survey_service: SurveyService = SurveyService()
        self.message_queue_service: MessageQueueService = MessageQueueService()
        self.survey_template_service: SurveyTemplateService = SurveyTemplateService()
        self.n8n: SimpleNamespace = SimpleNamespace(
            url=settings.n8n.n8n_webhook_url,
            header=settings.n8n.n8n_webhook_header,
            secret=settings.n8n.n8n_webhook_secret
        )
        self.tz: str = settings.timezone_zoneinfo
        self._register_handlers()

    def _register_handlers(self) -> None:
        """
        Registers command handlers in the router.

        Returns:
            None
        """
        # Commands for admins
        self.router.message(Command('reserve'))(self.reserve_command)
        self.router.message(Command('create_survey'))(
            self.create_survey_command
        )
        self.router.message(Command('bind_chat'))(self.bind_chat_command)
        self.router.message(Command('bind_thread'))(self.bind_thread_command)
        self.router.message(Command('unbind_thread'))(
            self.unbind_thread_command
        )
        self.router.message(Command('admin_list'))(self.admin_list_command)

        # Commands for creators
        self.router.message(Command('unbind_chat'))(self.unbind_chat_command)
        self.router.message(Command('add_admin'))(self.add_admin_command)
        self.router.message(Command('remove_admin'))(self.remove_admin_command)

    @Auth.required_admin
    async def reserve_command(self, message: Message) -> None:
        """
        Command handler for /reserve. Toggles the reservation status of a user by their callsign.

        Args:
            message (Message): Incoming message from the user.
        
        Returns:
            None
        """
        args: list[str] = message.text.split(maxsplit=1)

        if len(args) < 2 or not args[1].strip():
            await self.message_queue_service.send_message(
                chat_id=message.chat.id,
                text='❌ Пожалуйста, укажите позывной пользователя после команды.\n'
                     'Пример: `/reserve позывной`',
                parse_mode='Markdown',
                message_id=message.message_id
            )
            return

        callsign: str = args[1].strip()
        callsign: str = callsign.lower()

        user: User | None = \
            await self.user_service.get_user_by_callsign(callsign=callsign)

        if not user:
            await self.message_queue_service.send_message(
                chat_id=message.chat.id,
                text=f'❌ Пользователь с позывным `{callsign.capitalize()}` не найден.',
                parse_mode='Markdown',
                message_id=message.message_id
            )
            return

        user.reserved = not user.reserved
        await user.save()
        await self.message_queue_service.send_message(
            chat_id=message.chat.id,
            text=f'✅ Статус брони от опросов пользователя `{callsign.capitalize()}` изменён на: '
                 f'{"Есть" if user.reserved else "Нет"}.',
            parse_mode='Markdown',
            message_id=message.message_id
        )

    @Auth.required_admin
    @CreateSurvey.validate_survey_create
    async def create_survey_command(self, message: Message, title: str, ended_at: datetime) -> None:
        """
        Command handler for /create_survey.
        Creates a new survey using a default template and sends it to n8n.
        
        Args:
            message (Message): Incoming message from the user.
            title (str): Title of the survey.
            ended_at (datetime): End date and time of the survey.
        
        Returns:
            None
        """
        survey_template_obj: SurveyTemplate | None = \
            await self.survey_template_service.get_survey_template_by_name('default')

        if not survey_template_obj:
            await self.message_queue_service.send_message(
                chat_id=message.chat.id,
                text='❌ Шаблон опроса не найден в базе данных.',
                parse_mode='Markdown',
                message_id=message.message_id
            )
            return

        survey_json: str = json.dumps(survey_template_obj.json_content)

        if '{{title}}' not in survey_json or '{{ended_at}}' not in survey_json:
            await self.message_queue_service.send_message(
                chat_id=message.chat.id,
                text='❌ Шаблон опроса не содержит необходимых плейсхолдеров {{title}} или {{ended_at}}.',
                parse_mode='Markdown',
                message_id=message.message_id
            )
            return

        survey_json: str = survey_json.replace('{{title}}', title)
        survey_json: str = survey_json.replace('{{ended_at}}', ended_at.strftime('%Y-%m-%d %H:%M:%S'))

        survey_data: SurveyData = SurveyData(**json.loads(survey_json))

        headers: dict[str, str] = {
            'Content-Type': 'application/json',
            self.n8n.header: self.n8n.secret
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                        f'{self.n8n.url}/webhook/create-google-form',
                        json=survey_data.model_dump(),
                        headers=headers,
                ) as response:
                    if response.status == 200:
                        await self.message_queue_service.send_message(
                            chat_id=message.chat.id,
                            text='✅ Опрос успешно отправлен в n8n для создания!',
                            parse_mode='Markdown',
                            message_id=message.message_id
                        )

                    else:
                        error_text = await response.text()
                        await self.message_queue_service.send_message(
                            chat_id=message.chat.id,
                            text=(
                                f'❌ Не удалось создать опрос.\n\n'
                                f'Статус: {response.status},\nОтвет: {error_text}'
                            ),
                            parse_mode='Markdown',
                            message_id=message.message_id
                        )

            except aiohttp.ClientError as e:
                await self.message_queue_service.send_message(
                    chat_id=message.chat.id,
                    text=f'❌ Ошибка при подключении к n8n: {e}',
                    parse_mode='Markdown',
                    message_id=message.message_id
                )
                return

            except Exception as e:
                await self.message_queue_service.send_message(
                    chat_id=message.chat.id,
                    text=f'❌ Произошла ошибка при создании опроса: {e}',
                    parse_mode='Markdown',
                    message_id=message.message_id
                )
                return

    @Auth.required_admin
    @Auth.required_not_private_chat
    async def bind_chat_command(self, message: Message) -> None:
        """
        Command handler for /bind_chat. Binds the current chat to the database.
        Requires that no chat is already bound.

        Args:
            message (Message): Incoming message from the user.
        
        Returns:
            None
        """
        try:
            await self.chat_service.bind_chat(
                telegram_id=message.chat.id,
                chat_type=message.chat.type,
                title=message.chat.title or 'Без названия'
            )

            await self.message_queue_service.send_message(
                chat_id=message.chat.id,
                text='✅ Чат успешно привязан к базе данных.',
                parse_mode='Markdown',
                message_id=message.message_id
            )
        except ChatAlreadyBoundError as e:
            await self.message_queue_service.send_message(
                chat_id=message.chat.id,
                text=f'Не удалось привязать чат:\n{e}',
                parse_mode='Markdown',
                message_id=message.message_id
            )

    @Auth.required_creator
    @Auth.required_not_private_chat
    async def unbind_chat_command(self, message: Message) -> None:
        """
        Command handler for /unbind_chat. Unbinds the current chat from the database.

        Args:
            message (Message): Incoming message from the user.

        Returns:
            None
        """
        is_unbound: bool = await self.chat_service.unbind_chat(telegram_id=message.chat.id)

        if is_unbound:
            await self.message_queue_service.send_message(
                chat_id=message.chat.id,
                text='✅ Чат успешно отвязан от базы данных.',
                parse_mode='Markdown',
                message_id=message.message_id
            )
        else:
            await self.message_queue_service.send_message(
                chat_id=message.chat.id,
                text='❌ Не удалось отвязать чат.\nВозможно, он уже был отвязан ранее.',
                parse_mode='Markdown',
                message_id=message.message_id
            )

    @Auth.required_admin
    @Auth.required_not_private_chat
    async def bind_thread_command(self, message: Message) -> None:
        """
        Command handler for /bind_thread. Binds a thread in the current chat for survey notifications.
        Chat must be already bound and the command must be called within a thread.

        Args:
            message (Message): Incoming message from the user.
        
        Returns:
            None
        """
        chat: Chat | None = await self.chat_service.get_chat_by_telegram_id(message.chat.id)

        if not chat:
            await self.message_queue_service.send_message(
                chat_id=message.chat.id,
                text='❌ Этот чат не привязан к боту.',
                parse_mode='Markdown',
                message_id=message.message_id
            )
            return

        thread_id: int | None = message.message_thread_id

        if not thread_id:
            await self.message_queue_service.send_message(
                chat_id=message.chat.id,
                text='❌ Пожалуйста, вызовите эту команду в треде (ветке) чата, '
                     'который вы хотите назначить для оповещений по опросам.',
                parse_mode='Markdown',
                message_id=message.message_id
            )
            return

        await self.chat_service.set_thread_id(
            telegram_id=message.chat.id,
            thread_id=thread_id
        )

        await self.message_queue_service.send_message(
            chat_id=message.chat.id,
            text='✅ Тред успешно назначен для оповещений по опросам.',
            parse_mode='Markdown',
            message_id=message.message_id
        )

    @Auth.required_admin
    @Auth.required_not_private_chat
    async def unbind_thread_command(self, message: Message) -> None:
        """
        Command handler for /unbind_thread. Unbinds the thread in the current chat from survey notifications.

        Args:
            message (Message): Incoming message from the user.
        
        Returns:
            None
        """
        chat: Chat | None = await self.chat_service.get_chat_by_telegram_id(message.chat.id)

        if not chat:
            await self.message_queue_service.send_message(
                chat_id=message.chat.id,
                text='❌ Этот чат не привязан к боту.',
                parse_mode='Markdown',
                message_id=message.message_id
            )
            return

        await self.chat_service.delete_thread_id(
            telegram_id=message.chat.id
        )

        await self.message_queue_service.send_message(
            chat_id=message.chat.id,
            text='✅ Тред успешно отвязан от оповещений по опросам.',
            parse_mode='Markdown',
            message_id=message.message_id
        )

    @Auth.required_creator
    async def add_admin_command(self, message: Message) -> None:
        """
        Command handler for /add_admin. Grants admin role to a user by their callsign.

        Args:
            message (Message): Incoming message from the user.
        
        Returns:
            None
        """
        args: list[str] = message.text.split(maxsplit=1)

        if len(args) < 2 or not args[1].strip():
            await self.message_queue_service.send_message(
                chat_id=message.chat.id,
                text='❌ Пожалуйста, укажите позывной пользователя после команды.\n'
                     'Пример: `/add_admin позывной`',
                parse_mode='Markdown',
                message_id=message.message_id
            )
            return

        user: User | None = await self.user_service.get_user_by_callsign(args[1].strip().lower())

        if not user:
            await self.message_queue_service.send_message(
                chat_id=message.chat.id,
                text='❌ Пользователь не найден.',
                parse_mode='Markdown',
                message_id=message.message_id
            )
            return

        if user.is_creator:
            await self.message_queue_service.send_message(
                chat_id=message.chat.id,
                text='❌ Нельзя сделать создателя администратором.',
                parse_mode='Markdown',
                message_id=message.message_id
            )
            return

        if user.is_admin:
            await self.message_queue_service.send_message(
                chat_id=message.chat.id,
                text='❌ Пользователь уже является администратором.',
                parse_mode='Markdown',
                message_id=message.message_id
            )
            return

        await self.user_service.set_user_role(
            telegram_id=user.telegram_id,
            new_role=UserRole.ADMIN
        )

        await self.message_queue_service.send_message(
            chat_id=message.chat.id,
            text=f'✅ Пользователь `{user.callsign.capitalize()}` успешно добавлен в администраторы.',
            parse_mode='Markdown',
            message_id=message.message_id
        )

    @Auth.required_creator
    async def remove_admin_command(self, message: Message) -> None:
        """
        Command handler for /remove_admin. Revokes admin role from a user by their callsign.

        Args:
            message (Message): Incoming message from the user.

        Returns:
            None
        """
        args: list[str] = message.text.split(maxsplit=1)

        if len(args) < 2 or not args[1].strip():
            await self.message_queue_service.send_message(
                chat_id=message.chat.id,
                text='❌ Пожалуйста, укажите позывной пользователя после команды.\n'
                     'Пример: `/remove_admin позывной`',
                parse_mode='Markdown',
                message_id=message.message_id
            )
            return

        user: User | None = await self.user_service.get_user_by_callsign(args[1].strip().lower())

        if not user:
            await self.message_queue_service.send_message(
                chat_id=message.chat.id,
                text='❌ Пользователь не найден.',
                parse_mode='Markdown',
                message_id=message.message_id
            )
            return

        if user.is_creator:
            await self.message_queue_service.send_message(
                chat_id=message.chat.id,
                text='❌ Нельзя снять роль администратора с создателя.',
                parse_mode='Markdown',
                message_id=message.message_id
            )
            return

        if not user.is_admin:
            await self.message_queue_service.send_message(
                chat_id=message.chat.id,
                text='❌ Пользователь не является администратором.',
                parse_mode='Markdown',
                message_id=message.message_id
            )
            return

        await self.user_service.set_user_role(
            telegram_id=user.telegram_id,
            new_role=UserRole.USER
        )

        await self.message_queue_service.send_message(
            chat_id=message.chat.id,
            text=f'✅ Роль администратора у пользователя `{user.callsign.capitalize()}` успешно снята.',
            parse_mode='Markdown',
            message_id=message.message_id
        )

    @Auth.required_admin
    async def admin_list_command(self, message: Message) -> None:
        """
        Command handler for /admin_list. Sends a list of all admins with their callsigns and usernames.

        Args:
            message (Message): Incoming message from the user.
        
        Returns:
            None
        """
        admin_list: list[User] | None = await self.user_service.get_users_by_role(UserRole.ADMIN)

        if not admin_list:
            await self.message_queue_service.send_message(
                chat_id=message.chat.id,
                text='❌ Администраторы не назначены.',
                parse_mode='Markdown',
                message_id=message.message_id
            )
            return

        admin_lines: list[str] = []

        for idx, admin in enumerate(admin_list, 1):
            if admin.username:
                line = f'{idx}. [{admin.callsign.capitalize()}](https://t.me/{admin.username})'
            else:
                line = f'{idx}. `{admin.callsign.capitalize()}`'
            admin_lines.append(line)

        mas_message_length: int = 4096
        header: str = '👮‍♂️ *Список администраторов:*\n\n'
        chunk: str = header

        for line in admin_lines:
            line_with_newline: str = line + '\n'
            if len(chunk) + len(line_with_newline) > mas_message_length:
                await self.message_queue_service.send_message(
                    chat_id=message.chat.id,
                    text=chunk.rstrip(),
                    parse_mode='Markdown',
                    disable_web_page_preview=True,
                    message_id=message.message_id
                )
                chunk = ''
            if not chunk:
                chunk = line_with_newline
            else:
                chunk += line_with_newline

        if chunk.strip():
            await self.message_queue_service.send_message(
                chat_id=message.chat.id,
                text=chunk.rstrip(),
                parse_mode='Markdown',
                disable_web_page_preview=True,
                message_id=message.message_id
            )
