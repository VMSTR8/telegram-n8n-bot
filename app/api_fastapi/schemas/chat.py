from pydantic import BaseModel


class ChatSchema(BaseModel):
    """
    Schema representing a chat in the system.

    Attributes:
        id (int): Internal database ID of the chat
        telegram_id (int): Telegram ID of the chat
        title (str | None): Title of the chat
        chat_type (str): Type of the chat (e.g., private, group, supergroup)
        thread_id (int | None): Thread ID if applicable
    """
    id: int
    telegram_id: int
    title: str | None
    chat_type: str
    thread_id: int | None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "telegram_id": -1001234567890,
                "title": "My Telegram Chat",
                "chat_type": "supergroup",
                "thread_id": None
            }
        }
