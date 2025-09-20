from enum import Enum

from tortoise.models import Model
from tortoise import fields


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


class User(Model):
    """
    Модель пользователя Telegram бота
    """
    id = fields.IntField(pk=True)
    telegram_id = fields.BigIntField(unique=True, description='ID пользователя в Telegram')

    username = fields.CharField(max_length=255, null=True, description='Имя пользователя в Telegram')
    first_name = fields.CharField(max_length=255, null=True, description='Имя пользователя')
    last_name = fields.CharField(max_length=255, null=True, description='Фамилия пользователя')

    callsign = fields.CharField(max_length=20, unique=True, description='Позывной пользователя')
    role = fields.CharEnumField(UserRole, default=UserRole.USER, description='Роль пользователя')

    is_active = fields.BooleanField(default=True, description='Активен ли пользователь')
    created_at = fields.DatetimeField(auto_now_add=True, description='Дата и время создания записи')
    updated_at = fields.DatetimeField(auto_now=True, description='Дата и время последнего обновления записи')

    reserved = fields.BooleanField(default=False, description='Есть ли бронь от опросов у пользователя')

    class Meta:
        table = "users"
        table_description = "Таблица пользователей Telegram бота"

    def __str__(self) -> str:
        """Строковое представление пользователя """
        return f'User {self.telegram_id}: {self.role}'

    @property
    def is_creator(self) -> bool:
        """Проверяет, является ли пользователь создателем бота"""
        return self.role == UserRole.CREATOR

    @property
    def is_admin(self) -> bool:
        """Проверяет, является ли пользователь администратором"""
        return self.role in [UserRole.ADMIN, UserRole.CREATOR]

    @property
    def is_reserved(self) -> bool:
        """Проверяет, есть ли у пользователя бронь от опросов"""
        return self.reserved
