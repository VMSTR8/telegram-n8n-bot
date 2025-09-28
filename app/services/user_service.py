from typing import Optional, List
from datetime import datetime

from app.models import User, UserRole
from config.settings import settings


class UserService:
    """
    Сервис для управления пользователями.
    """
    @staticmethod
    async def get_user_by_telegram_id(telegram_id: int) -> Optional[User]:
        """
        Получить пользователя по его Telegram ID.

        :param telegram_id: Telegram ID пользователя.
        :return: User | None - объект пользователя или None, если пользователь не найден.
        """
        return await User.filter(telegram_id=telegram_id).first()

    @staticmethod
    async def get_user_by_callsign(callsign: str) -> Optional[User]:
        """
        Получить пользователя по его позывному.

        :param callsign: Позывной пользователя.
        :return: User | None - объект пользователя или None, если пользователь не найден.
        """
        return await User.filter(callsign=callsign).first()

    @staticmethod
    async def create_user(
            telegram_id: int,
            callsign: str,
            role: UserRole = UserRole.USER,
            first_name: Optional[str] = None,
            last_name: Optional[str] = None,
            username: Optional[str] = None,
    ) -> User:
        """
        Создает нового пользователя.

        :param telegram_id: ID пользователя в Telegram
        :param callsign: Позывной пользователя
        :param role: Роль пользователя (по умолчанию USER)
        :param first_name: Имя пользователя (если есть)
        :param last_name: Фамилия пользователя (если есть)
        :param username: Никнейм пользователя в Telegram (если есть)
        :return: Объект User
        """

        user = await User.create(
            telegram_id=telegram_id,
            callsign=callsign,
            role=role,
            first_name=first_name,
            last_name=last_name,
            username=username
        )

        return user
    
    @staticmethod
    async def update_user(user_telegram_id: int, **data) -> User:
        """
        Обновляет данные пользователя.

        :param user_telegram_id: Telegram ID пользователя для обновления
        :param data: Ключевые слова аргументы с данными для обновления
        :return: Объект User после обновления
        """
        user = await User.get(telegram_id=user_telegram_id)
        for key, value in data.items():
            setattr(user, key, value)
        await user.save()
        return user

    async def set_user_role(
            self,
            telegram_id: int,
            new_role: UserRole
    ) -> bool:
        """
        Устанавливает роль пользователя.

        :param telegram_id: ID пользователя в Telegram
        :param new_role: Новая роль пользователя (USER, ADMIN)
        :return: bool - True, если роль успешно установлена, иначе False
        """
        user = await self.get_user_by_telegram_id(telegram_id=telegram_id)
        if not user:
            return False

        user.role = new_role
        user.updated_at = datetime.now(tz=settings.timezone_zoneinfo)
        await user.save()

        return True

    async def set_user_reserved_status(
            self,
            telegram_id: int
    ) -> bool:
        """
        Устанавливает или снимает бронь от опросов у пользователя.

        :param telegram_id: ID пользователя в Telegram
        :return: bool - True, если статус успешно установлен, иначе False
        """
        user = await self.get_user_by_telegram_id(telegram_id=telegram_id)
        if not user:
            return False

        user.reserved = not user.reserved
        user.updated_at = datetime.now(tz=settings.timezone_zoneinfo)
        await user.save()

        return True

    async def set_user_active_status(
            self,
            telegram_id: int
    ) -> bool:
        """
        Деактивирует или активирует пользователя.

        :param telegram_id: ID пользователя в Telegram
        :return: bool - True, если пользователь успешно деактивирован, иначе False
        """
        user = await self.get_user_by_telegram_id(telegram_id=telegram_id)
        if not user:
            return False

        user.active = not user.active
        user.updated_at = datetime.now(tz=settings.timezone_zoneinfo)
        await user.save()

        return True

    @staticmethod
    async def get_users_by_role(
            role: UserRole
    ) -> List[User]:
        """
        Получает список активных пользователей по их роли.

        :param role: Роль пользователя (USER, ADMIN)
        :return: list[User] - Список пользователей с указанной ролью
        """
        return await User.filter(role=role, active=True).all()

    @staticmethod
    async def get_users_without_reservation() -> List[User]:
        """
        Получает список пользователей без бронирования.
        
        :return: list[User] - Список пользователей без бронирования
        """
        return await User.filter(reserved=False, active=True).all()
