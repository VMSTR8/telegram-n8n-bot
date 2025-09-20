from pydantic import BaseModel
from enum import Enum
from typing import Optional
from datetime import datetime


class UserRole(str, Enum):
    """
    Роли пользователей
    - CREATOR: Создатель бота, имеет все права
    - ADMIN: Администратор, имеет расширенные права
    - USER: Обычный пользователь, имеет базовые права
    """
    CREATOR = 'creator'
    ADMIN = 'admin'
    USER = 'user'


class UserSchema(BaseModel):
    """
    Схема пользователя Telegram бота
    """
    id: int
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    callsign: str
    role: UserRole = UserRole.USER
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    reserved: bool = False

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "telegram_id": 123456789,
                "username": "johndoe",
                "first_name": "John",
                "last_name": "Doe",
                "callsign": "JD123",
                "role": "user",
                "is_active": True,
                "created_at": "2023-01-01T12:00:00",
                "updated_at": "2023-01-02T12:00:00",
                "reserved": False
            }
        }
