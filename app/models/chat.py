from tortoise.models import Model
from tortoise import fields


class Chat(Model):
    """
    Модель чата Telegram бота
    """
    id = fields.IntField(pk=True)
    chat_telegram_id = fields.BigIntField(unique=True, description='ID чата в Telegram')
    title = fields.CharField(max_length=255, null=True, description='Название чата')
    type = fields.CharField(max_length=50, description='Тип чата (private, group, supergroup, channel)')
    thread_id = fields.BigIntField(null=True, description='ID треда в чате, если применимо')

    class Meta:
        table = "chats"
        table_description = "Таблица чатов Telegram бота"

    def __str__(self) -> str:
        """Строковое представление чата"""
        return f'Chat {self.chat_telegram_id}: {self.title or "No Title"}'

    @property
    def is_thread_enabled(self) -> bool:
        """Проверяет, является ли чат тредом (форумным чатом)"""
        return self.thread_id is not None
