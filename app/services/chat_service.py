from typing import Optional
from tortoise.transactions import in_transaction
from app.models import Chat


class ChatAlreadyBoundError(Exception):
    """
    Exception raised when trying to bind a chat
    but a chat is already bound in the database.
    """
    pass


class ChatService:
    """
    Service class for managing chat-related operations.
    """

    @staticmethod
    async def get_chat_by_telegram_id(
            telegram_id: int
    ) -> Optional[Chat]:
        """
        Gets a chat by its Telegram ID.

        :param telegram_id: Telegram ID of the chat
        :return: Optional[Chat] - Chat object or None if not found
        """
        return await Chat.filter(telegram_id=telegram_id).first()

    async def bind_chat(
        self,
        telegram_id: int,
        chat_type: str,
        title: Optional[str] = None,
    ) -> Chat:
        """
        Binds only one chat to the database. If there is already a bound chat, raises ChatAlreadyBoundError.
        Race condition protection via transaction.

        :param telegram_id: Telegram chat ID
        :param chat_type: Chat type (private, group, supergroup, channel)
        :param title: Chat title (if any)
        :return: Chat - created chat object
        :raises ChatAlreadyBoundError: if a chat is already bound
        """
        async with in_transaction():
            already_exists = await Chat.exists()
            if already_exists:
                raise ChatAlreadyBoundError(
                    '❌ В базе уже есть привязанный чат. Можно привязать только один.'
                )

            chat = await Chat.create(
                telegram_id=telegram_id,
                chat_type=chat_type,
                title=title
            )

            return chat

    async def unbind_chat(
            self,
            telegram_id: int
    ) -> bool:
        """
        Unbinds a chat by its Telegram ID.

        :param telegram_id: Telegram ID of the chat
        :return: bool - True if the chat was removed, False if not found
        """
        chat = await self.get_chat_by_telegram_id(telegram_id=telegram_id)
        if not chat:
            return False

        await chat.delete()
        return True

    async def set_thread_id(
            self,
            telegram_id: int,
            thread_id: int
    ) -> bool:
        """
        Sets the thread ID for the chat.

        :param telegram_id: Telegram chat ID
        :param thread_id: Thread ID in the chat
        :return: bool - True if the thread was set, False if the chat was not found
        """
        chat = await self.get_chat_by_telegram_id(telegram_id=telegram_id)
        if not chat:
            return False

        chat.thread_id = thread_id
        await chat.save()
        return True

    async def delete_thread_id(
            self,
            telegram_id: int
    ) -> bool:
        """
        Deletes the thread ID for the chat.

        :param telegram_id: Telegram chat ID
        :return: bool - True if the thread was removed, False if not found
        """
        chat = await self.get_chat_by_telegram_id(telegram_id=telegram_id)
        if not chat:
            return False

        chat.thread_id = None
        await chat.save()
        return True
