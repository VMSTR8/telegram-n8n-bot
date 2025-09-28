from aiogram import Router
from aiogram.types import ChatMemberUpdated
from aiogram.filters import ChatMemberUpdatedFilter, IS_NOT_MEMBER, IS_MEMBER

from app.services import UserService, ChatService


class SystemHandlers:
    """
    Handlers for system events like user joining or leaving a chat.
    """

    def __init__(self):
        self.router = Router()
        self.user_service = UserService()
        self.chat_service = ChatService()
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

    async def on_user_join(self, event: ChatMemberUpdated) -> None:
        """
        Handle user joining a chat.

        :param event: ChatMemberUpdated event
        :return: None
        """
        user = event.new_chat_member.user
        chat = event.chat
        bot = event.bot

        chat_exists = await self.chat_service.get_chat_by_telegram_id(chat.id)
        if not chat_exists:
            return

        if user.is_bot:
            return

        user_exists = await self.user_service.get_user_by_telegram_id(user.id)

        if user_exists:
            await bot.send_message(
                chat_id=chat.id,
                text=f'Lorum Ipsum!',
                parse_mode='Markdown'
            )

        if not user_exists:
            await bot.send_message(
                chat_id=chat.id,
                text=f'Lorum Impsum...',
                parse_mode='Markdown'
            )

    async def on_user_leave(self, event: ChatMemberUpdated) -> None:
        """
        Handle user leaving a chat.

        :param event: ChatMemberUpdated event
        :return: None
        """
        pass
