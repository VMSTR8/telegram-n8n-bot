from enum import Enum

from tortoise.models import Model
from tortoise import fields


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


class User(Model):
    """
    Model representing a Telegram bot user.
    """
    id = fields.IntField(pk=True)
    telegram_id = fields.BigIntField(unique=True, description='Telegram ID of the user')

    username = fields.CharField(max_length=255, null=True, description='Username in Telegram')
    first_name = fields.CharField(max_length=255, null=True, description='Name of the user')
    last_name = fields.CharField(max_length=255, null=True, description='Last name of the user')

    callsign = fields.CharField(max_length=20, unique=True, description='User callsign')
    role = fields.CharEnumField(UserRole, default=UserRole.USER, description='User role')

    active = fields.BooleanField(default=True, description='Active status of the user')
    created_at = fields.DatetimeField(auto_now_add=True, description='Date and time of record creation')
    updated_at = fields.DatetimeField(auto_now=True, description='Date and time of last record update')

    reserved = fields.BooleanField(default=False, description='Is there a reservation from surveys for the user')

    class Meta:
        table = "users"
        table_description = "Table of Telegram bot users"

    def __str__(self) -> str:
        """String representation of the user"""
        return f'User {self.telegram_id}: {self.role}'

    @property
    def is_creator(self) -> bool:
        """Checks if the user is the bot creator"""
        return self.role == UserRole.CREATOR

    @property
    def is_admin(self) -> bool:
        """Checks if the user is an administrator"""
        return self.role in [UserRole.ADMIN, UserRole.CREATOR]

    @property
    def is_reserved(self) -> bool:
        """Checks if the user has a reservation from surveys"""
        return self.reserved
