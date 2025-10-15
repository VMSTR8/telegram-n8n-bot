from typing import Any, Optional, Tuple

from aiogram import Router
from aiogram.filters import ChatMemberUpdatedFilter, IS_MEMBER, IS_NOT_MEMBER
from aiogram.types import ChatMemberUpdated

from app.models import UserRole

from app.services import UserService, ChatService, PenaltyService, MessageQueueService


class SystemHandlers:
    """
    Handlers for system events like user joining or leaving a chat.
    """

    def __init__(self):
        self.router = Router()
        self.user_service = UserService()
        self.chat_service = ChatService()
        self.penalty_service = PenaltyService()
        self.message_queue_service = MessageQueueService()
        self._register_handlers()

    def _register_handlers(self) -> None:
        """
        Register handlers for user join and leave events.

        :return: None
        """
        self.router.chat_member.register(
            self.on_user_join,
            ChatMemberUpdatedFilter(
                member_status_changed=IS_NOT_MEMBER >> IS_MEMBER)
        )

        self.router.chat_member.register(
            self.on_user_leave,
            ChatMemberUpdatedFilter(
                member_status_changed=IS_MEMBER >> IS_NOT_MEMBER)
        )

    async def _extract_event_context(
            self,
            event: ChatMemberUpdated,
            is_join: bool = True
    ) -> Optional[Tuple[Any, Any, Any, Any]]:
        """
        Extract user, chat, bot, and user existence from the event.

        :param event: ChatMemberUpdated event
        :param is_join: Boolean indicating if the event is a join event
        :return: Tuple of user, chat, bot, and user existence or None
        """
        if is_join:
            user = event.new_chat_member.user
        else:
            user = event.old_chat_member.user
        chat = event.chat
        bot = event.bot

        chat_exists = await self.chat_service.get_chat_by_telegram_id(chat.id)
        if not chat_exists or user.is_bot:
            return None

        user_exists = await self.user_service.get_user_by_telegram_id(user.id)

        return user, chat, bot, user_exists

    async def on_user_join(self, event: ChatMemberUpdated) -> None:
        """
        Handle user joining a chat.

        :param event: ChatMemberUpdated event
        :return: None
        """
        result = await self._extract_event_context(event, is_join=True)
        if not result:
            return
        user, chat, bot, user_exists = result

        if user_exists:
            # Reactivate user if they were previously deactivated
            # This can happen if they left/banned and rejoined the chat
            await self.user_service.activate_user(telegram_id=user.id)
            # Remove all penalties upon rejoining
            await self.penalty_service.delete_user_penalties(user=user_exists)
            
            await self.message_queue_service.send_message(
                chat_id=chat.id,
                text=f'Добро пожаловать в чат, {user_exists.callsign.capitalize()}!\n\n'
                     f'Вы уже зарегистрированы в боте, поэтому вам доступны '
                     f'все слэш-команды. Справка доступна через вызов '
                     f'`/help`.\n\n'
                     f'Вовремя проходите опросы, о которых оповещает бот, '
                     f'чтобы не получить штрафные баллы.\n'
                     f'Если накопите 3 штрафных балла за пол года, вы будете '
                     f'исключены из команды без права возврата. Каждое 01 января '
                     f'и 01 июля штрафные баллы сбрасываются автоматически.\n\n'
                     f'В исключительных случаях, когда вы не сможете проходить опросы, '
                     f'сообщите об этом командиру команды или заместителю, вам '
                     f'выдадут бронь от прохождения опросов.',
                parse_mode='Markdown'
            )

        if not user_exists:
            await self.message_queue_service.send_message(
                chat_id=chat.id,
                text=f'Добро пожаловать в чат, {user.full_name.replace('_', r'\_')}!\n\n'
                     f'Вы еще не зарегистрированы в боте, поэтому вам необходимо '
                     f'пройти регистрацию, используя команду:\n\n'
                     f'`/reg позывной`\n\n'
                     f'Позывной не должен содержать ничего, кроме латинских букв, '
                     f'и быть длиннее 20 символов.\n\n'
                     f'Если вы проигнорируете регистрацию в течение 24 часов с момента '
                     f'вступления в чат, вы будете удалены из него командиром команды и '
                     f'ваше вступление в команду будет аннулировано.\n\n'
                     f'После регистрации вам станут доступны все слэш-команды бота, '
                     f'узнать о которых вы можете, вызвав команду `/help`.\n\n'
                     f'Вовремя проходите опросы, о которых оповещает бот, '
                     f'чтобы не получить штрафные баллы.\n'
                     f'Если накопите 3 штрафных балла за пол года, вы будете '
                     f'исключены из команды без права возврата. Каждое 01 января '
                     f'и 01 июля штрафные баллы сбрасываются автоматически.\n\n'
                     f'В исключительных случаях, когда вы не сможете проходить опросы, '
                     f'сообщите об этом командиру команды или заместителю, вам '
                     f'выдадут бронь от прохождения опросов.',
                parse_mode='Markdown'
            )

    async def on_user_leave(self, event: ChatMemberUpdated) -> None:
        """
        Handle user leaving a chat.

        :param event: ChatMemberUpdated event
        :return: None
        """
        result = await self._extract_event_context(event, is_join=False)
        if not result:
            return
        user, chat, bot, user_exists = result

        if not user_exists:
            text = f'{user.full_name.replace('_', r'\_')} удален(а) из чата.'
        else:
            text = f'`{user_exists.callsign.capitalize()}` удален(а) из чата.'

        await self.user_service.deactivate_user(telegram_id=user.id)

        await self.user_service.set_user_role(
            telegram_id=user.id,
            new_role=UserRole.USER
        )

        await self.message_queue_service.send_message(
            chat_id=chat.id,
            text=text,
            parse_mode='Markdown'
        )
