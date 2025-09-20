from pydantic import BaseModel


class ChatSchema(BaseModel):
    """
    Схема чата Telegram.
    """
    id: int
    chat_telegram_id: int
    title: str | None
    type: str
    thread_id: int | None

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "chat_telegram_id": -1001234567890,
                "title": "My Telegram Chat",
                "type": "supergroup",
                "thread_id": None
            }
        }
