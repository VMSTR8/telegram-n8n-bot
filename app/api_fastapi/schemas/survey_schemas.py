from pydantic import BaseModel


class UserInfo(BaseModel):
    """Schema representing user information (telegram_id, username, etc.)"""
    telegram_id: int
    username: str | None
    first_name: str | None
    last_name: str | None


class UserPenaltyInfo(BaseModel):
    """Schema representing user penalty information."""
    telegram_id: int
    username: str | None
    callsign: str
    penalty_count: int


class TelegramMessage(BaseModel):
    """Schema representing a Telegram message."""
    chat_id: int
    message_thread_id: int | None = None
    text: str
    disable_web_page_preview: bool | None = False
    parse_mode: str | None = None


class WebhookResponse(BaseModel):
    """Schema representing a webhook response."""
    success: str
    data: dict
    users_with_three_penalties: list[UserPenaltyInfo] | None = None
