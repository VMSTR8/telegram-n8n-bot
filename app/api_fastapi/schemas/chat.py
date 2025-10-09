from pydantic import BaseModel


class ChatSchema(BaseModel):
    """
    Schema representing a chat in the system.
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
