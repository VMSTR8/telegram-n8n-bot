from typing import Optional

from app.models import Chat


class ChatService:
    """
    Сервис для управления чатами Telegram бота
    """
    
    @staticmethod
    async def get_chat_by_telegram_id(
            telegram_id: int
    ) -> Optional[Chat]:
        """
        Получает чат по его Telegram ID.

        :param telegram_id: ID чата в Telegram
        :return: Optional[Chat] - объект чата или None, если не найден
        """
        return await Chat.filter(telegram_id=telegram_id).first()

    async def bind_chat(
            self,
            telegram_id: int,
            chat_type: str,
            title: Optional[str] = None,
    ) -> Chat:
        """
        Привязывает новый чат к базе данных, если он ещё не существует.

        :param telegram_id: ID чата в Telegram
        :param chat_type: Тип чата (private, group, supergroup, channel)
        :param title: Название чата (если есть)
        :return: Chat - созданный или существующий объект чата
        """
        existing_chat = await self.get_chat_by_telegram_id(telegram_id=telegram_id)
        if existing_chat:
            return existing_chat

        chat = await Chat.create(
            telegram_id=telegram_id,
            chat_type=chat_type,
            title=title
        )
        return chat
    
    async def update_chat_telegram_id(
            self,
            chat_id: int,
            new_telegram_id: int
    ) -> Optional[Chat]:
        """
        Обновляет Telegram ID чата по его внутреннему ID.

        :param chat_id: Внутренний ID чата в базе данных
        :param new_telegram_id: Новый ID чата в Telegram
        :return: Optional[Chat] - обновленный объект чата или None, если чат не найден
        """
        chat = await Chat.filter(id=chat_id).first()
        if not chat:
            return None

        chat.telegram_id = new_telegram_id
        await chat.save()
        return chat

    async def unbind_chat(
            self,
            telegram_id: int
    ) -> bool:
        """
        Отвязывает чат от базы данных, удаляя его.

        :param telegram_id: ID чата в Telegram
        :return: bool - True, если чат был удален, False если чат не найден
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
        Устанавливает ID треда для чата.

        :param telegram_id: ID чата в Telegram
        :param thread_id: ID треда в чате
        :return: bool - True, если тред был установлен, False если чат не найден
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
        Удаляет ID треда для чата.
        
        :param telegram_id: ID чата в Telegram
        :return: bool - True, если тред был удален, False если чат не найден
        """
        chat = await self.get_chat_by_telegram_id(telegram_id=telegram_id)
        if not chat:
            return False

        chat.thread_id = None
        await chat.save()
        return True
