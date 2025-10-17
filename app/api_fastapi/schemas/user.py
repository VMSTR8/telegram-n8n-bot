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

    Attributes:
        id (int): Internal database ID of the user
        telegram_id (int): Telegram ID of the user
        username (str | None): Telegram username of the user
        first_name (str | None): First name of the user
        last_name (str | None): Last name of the user
        callsign (str): Unique callsign for the user
        role (UserRole): Role of the user in the system
        active (bool): Indicates if the user is active
        created_at (datetime): Timestamp when the user was created
        updated_at (datetime): Timestamp when the user was last updated
        reserved (bool): Indicates if the user is reserved
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
        from_attributes = True
        json_schema_extra = {
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
