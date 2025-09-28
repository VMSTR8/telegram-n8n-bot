from tortoise.models import Model
from tortoise import fields


class Chat(Model):
    """
    Model representing a Telegram chat.
    """
    id = fields.IntField(pk=True)
    telegram_id = fields.BigIntField(unique=True, description='Telegram ID чата')
    title = fields.CharField(max_length=255, null=True, description='Chat title, if any')
    chat_type = fields.CharField(max_length=50, description='Chat type (private, group, supergroup, channel)')
    thread_id = fields.BigIntField(null=True, description='Thread ID in the chat, if applicable')

    class Meta:
        table = "chats"
        table_description = "Table of Telegram bot chats"

    def __str__(self) -> str:
        """String representation of the chat"""
        return f'Chat {self.telegram_id}: {self.title or "No Title"}'

    @property
    def is_thread_enabled(self) -> bool:
        """Checks if the chat is a thread (forum chat)"""
        return self.thread_id is not None
