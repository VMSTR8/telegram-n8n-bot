from typing import Optional, List

from app.models import User, UserRole


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

    async def is_callsign_taken(self, callsign: str) -> bool:
        """
        Проверить, занят ли позывной.
        :param callsign: Позывной для проверки.
        :return: bool - True, если позывной занят, иначе False.
        """
        user = await self.get_user_by_callsign(callsign=callsign)
        return user is not None

    @staticmethod
    async def create_user(
            telegram_id: int,
            callsign: str,
            first_name: Optional[str] = None,
            last_name: Optional[str] = None,
            username: Optional[str] = None,
    ) -> User:
        """
        Создает нового пользователя.
        :param telegram_id: ID пользователя в Telegram
        :param callsign: Позывной пользователя
        :param first_name: Имя пользователя (если есть)
        :param last_name: Фамилия пользователя (если есть)
        :param username: Никнейм пользователя в Telegram (если есть)
        :return: Объект User
        """

        # TODO сделать валидацию формата позывного, то, что позывной не занят

        user = await User.create(
            telegram_id=telegram_id,
            callsign=callsign,
            first_name=first_name,
            last_name=last_name,
            username=username
        )

        return user

    @staticmethod
    async def update_user_profile(
            telegram_id: int,
            callsign: str,
            first_name: Optional[str] = None,
            last_name: Optional[str] = None,
            username: Optional[str] = None,
    ) -> Optional[User]:
        """
        Обновляет профиль пользователя.
        :param telegram_id: ID пользователя в Telegram
        :param callsign: Позывной пользователя
        :param first_name: Имя пользователя (если есть)
        :param last_name: Фамилия пользователя (если есть)
        :param username: Никнейм пользователя в Telegram (если есть)
        :return: Объект User или None, если пользователь не найден
        """
        pass

    @staticmethod
    async def set_user_role(
            telegram_id: int,
            role: UserRole
    ) -> bool:
        """
        Устанавливает роль пользователя.
        :param telegram_id: ID пользователя в Telegram
        :param role: Роль пользователя (USER, ADMIN)
        :return: bool - True, если роль успешно установлена, иначе False
        """
        pass

    @staticmethod
    async def set_user_reserved_status(
            telegram_id: int,
            new_is_reserved: bool
    ) -> bool:
        """
        Устанавливает статус бронирования пользователя.
        :param telegram_id: ID пользователя в Telegram
        :param new_is_reserved: Новый статус бронирования (True или False)
        :return: bool - True, если статус успешно установлен, иначе False
        """
        pass

    @staticmethod
    async def deactivate_user(
            telegram_id: int
    ) -> bool:
        """
        Деактивирует пользователя.
        :param telegram_id: ID пользователя в Telegram
        :return: bool - True, если пользователь успешно деактивирован, иначе False
        """
        pass

    @staticmethod
    async def get_users_by_role(
            role: UserRole
    ) -> List[User]:
        """
        Получает список пользователей по их роли.
        :param role: Роль пользователя (USER, ADMIN)
        :return: list[User] - Список пользователей с указанной ролью
        """
        pass

    @staticmethod
    async def get_users_without_reservation() -> List[User]:
        """
        Получает список пользователей без бронирования.
        :return: list[User] - Список пользователей без бронирования
        """
        pass
