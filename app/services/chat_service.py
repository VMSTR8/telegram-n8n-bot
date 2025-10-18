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

    Methods:
        get_bound_chat: Gets the currently bound chat.
        get_chat_by_telegram_id: Gets a chat by its Telegram ID.
        bind_chat: Binds only one chat to the database. If there is already a bound chat, raises ChatAlreadyBoundError.
        unbind_chat: Unbinds a chat by its Telegram ID.
        set_thread_id: Sets the thread ID for the chat.
        delete_thread_id: Deletes the thread ID for the chat.
    """

    @staticmethod
    async def get_bound_chat() -> Chat | None:
        """
        Gets the currently bound chat.

        Returns:
            Chat object or None if no chat is bound
        """
        return await Chat.all().first()

    @staticmethod
    async def get_chat_by_telegram_id(
            telegram_id: int
    ) -> Chat | None:
        """
        Gets a chat by its Telegram ID.

        Args:
            telegram_id (int): Telegram chat ID
        
        Returns:
            Chat object or None if not found
        """
        return await Chat.filter(telegram_id=telegram_id).first()

    @staticmethod
    async def bind_chat(
            telegram_id: int,
            chat_type: str,
            title: str | None = None,
    ) -> Chat:
        """
        Binds only one chat to the database. If there is already a bound chat, raises ChatAlreadyBoundError.
        Race condition protection via transaction.

        Args:
            telegram_id (int): Telegram chat ID
            chat_type (str): Type of the chat (e.g., 'private', 'group', 'supergroup', 'channel')
            title (str | None): Title of the chat (optional)

        Raises:
            ChatAlreadyBoundError: If there is already a bound chat in the database
        
        Returns:
            Chat object that was created
        """
        async with in_transaction():
            already_exists: bool = await Chat.exists()
            if already_exists:
                raise ChatAlreadyBoundError(
                    '❌ В базе уже есть привязанный чат. Можно привязать только один.'
                )

            chat: Chat = await Chat.create(
                telegram_id=telegram_id,
                chat_type=chat_type,
                title=title
            )

            return chat

    @staticmethod
    async def unbind_chat() -> int:
        """
        Unbinds the currently bound chat by deleting it from the database.

        Returns:
            Number of deleted chats
        """
        return await Chat.all().delete()

    async def set_thread_id(
            self,
            telegram_id: int,
            thread_id: int
    ) -> bool:
        """
        Sets the thread ID for the chat.

        Args:
            telegram_id (int): Telegram chat ID
            thread_id (int): Thread ID to set

        Returns:
            True if the thread ID was set, False if the chat was not found
        """
        chat: Chat | None = await self.get_chat_by_telegram_id(telegram_id=telegram_id)
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

        Args:
            telegram_id (int): Telegram chat ID

        Returns:
            True if the thread ID was deleted, False if not found
        """
        chat: Chat | None = await self.get_chat_by_telegram_id(telegram_id=telegram_id)
        if not chat:
            return False

        chat.thread_id = None
        await chat.save()
        return True
