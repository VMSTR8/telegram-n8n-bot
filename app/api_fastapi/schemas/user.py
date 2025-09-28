from pydantic import BaseModel
from enum import Enum
from typing import Optional
from datetime import datetime


class UserRole(str, Enum):
    """
    User roles
    - CREATOR: Bot creator, has all permissions
    - ADMIN: Administrator, has extended permissions
    - USER: Regular user, has basic permissions
    """
    CREATOR = 'creator'
    ADMIN = 'admin'
    USER = 'user'


class UserSchema(BaseModel):
    """
    User schema for the Telegram bot
    """
    id: int
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    callsign: str
    role: UserRole = UserRole.USER
    active: bool = True
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
                "active": True,
                "created_at": "2023-01-01T12:00:00",
                "updated_at": "2023-01-02T12:00:00",
                "reserved": False
            }
        }
