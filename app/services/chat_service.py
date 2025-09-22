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
        Получает чат по его Telegram ID
        :param telegram_id: ID чата в Telegram
        :return: Optional[Chat] - объект чата или None, если не найден
        """
        return await Chat.filter(telegram_id=telegram_id).first()

    async def bind_or_update_bound_chat(
            self,
            telegram_id: int,
            chat_type: str,
            title: Optional[str] = None,
    ) -> Chat:
        """
        Привязывает чат к базе данных или обновляет его данные, если он уже привязан
        :param telegram_id: ID чата в Telegram
        :param chat_type: Тип чата (private, group, supergroup, channel)
        :param title: Название чата (если есть)
        :return: Chat - объект чата
        """
        chat_exist = await self.get_chat_by_telegram_id(telegram_id=telegram_id)

        if chat_exist:
            chat_exist.chat_type = chat_type
            chat_exist.title = title
            await chat_exist.save()
            
            return chat_exist

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
        Отвязывает чат от базы данных, удаляя его
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
        Устанавливает ID треда для чата
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
        Удаляет ID треда для чата
        :param telegram_id: ID чата в Telegram
        :return: bool - True, если тред был удален, False если чат не найден
        """
        chat = await self.get_chat_by_telegram_id(telegram_id=telegram_id)
        if not chat:
            return False

        chat.thread_id = None
        await chat.save()
        return True
