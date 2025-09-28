from typing import Optional, List
from datetime import datetime

from app.models import User, UserRole
from config.settings import settings


class UserService:
    """
    Service for managing Telegram bot users.
    """
    @staticmethod
    async def get_user_by_telegram_id(telegram_id: int) -> Optional[User]:
        """
        Get user by their Telegram ID.

        :param telegram_id: Telegram ID of the user.
        :return: User | None - user object or None if not found.
        """
        return await User.filter(telegram_id=telegram_id).first()

    @staticmethod
    async def get_user_by_callsign(callsign: str) -> Optional[User]:
        """
        Get user by their callsign.

        :param callsign: Callsign of the user.
        :return: User | None - user object or None if not found.
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
        Creates a new user.

        :param telegram_id: Telegram ID of the user
        :param callsign: Callsign of the user
        :param role: Role of the user (default is USER)
        :param first_name: First name of the user (if available)
        :param last_name: Last name of the user (if available)
        :param username: Username of the user in Telegram (if available)
        :return: User object
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
        Updates user information.

        :param user_telegram_id: Telegram ID of the user to update
        :param data: Keyword arguments with data to update
        :return: User object after update
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
        Sets the user's role.

        :param telegram_id: Telegram ID of the user
        :param new_role: New role of the user (USER, ADMIN)
        :return: bool - True if the role was successfully set, otherwise False
        """
        user = await self.get_user_by_telegram_id(telegram_id=telegram_id)
        if not user:
            return False

        user.role = new_role
        user.updated_at = datetime.now(tz=settings.timezone_zoneinfo)
        await user.save()

        return True

    @staticmethod
    async def get_users_by_role(
            role: UserRole
    ) -> List[User]:
        """
        Get a list of active users by their role.

        :param role: Role of the user (USER, ADMIN)
        :return: list[User] - List of users with the specified role
        """
        return await User.filter(role=role, active=True).all()

    @staticmethod
    async def get_users_without_reservation() -> List[User]:
        """
        Get a list of users without reservations.

        :return: list[User] - List of users without reservations
        """
        return await User.filter(reserved=False, active=True).all()
