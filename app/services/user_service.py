from datetime import datetime

from app.models import User, UserRole
from config.settings import settings


class UserService:
    """
    Service for managing Telegram bot users.

    Methods:
        get_user_by_telegram_id: Get user by their Telegram ID.
        get_user_by_callsign: Get user by their callsign.
        get_active_user_by_callsign_exclude_creator: Get active user by their callsign excluding creators.
        create_user: Creates a new user.
        update_user: Updates user information.
        set_user_role: Sets the user's role.
        activate_user: Activates a user.
        deactivate_user: Deactivates a user.
        get_users_by_role: Get a list of active users by their role.
        get_users_without_reservation_exclude_creators: Get a list of active users without reservations (creators are excluded).
    """

    @staticmethod
    async def get_user_by_telegram_id(telegram_id: int) -> User | None:
        """
        Get user by their Telegram ID.

        Args:
            telegram_id (int): Telegram ID of the user.
        
        Returns:
            User | None: User object or None if not found.
        """
        return await User.filter(telegram_id=telegram_id).first()

    @staticmethod
    async def get_user_by_callsign(callsign: str) -> User | None:
        """
        Get user by their callsign.

        Args:
            callsign (str): Callsign of the user.
        
        Returns:
            User | None: User object or None if not found.
        """
        return await User.filter(callsign=callsign).first()

    @staticmethod
    async def get_active_user_by_callsign_exclude_creator(callsign: str) -> User | None:
        """
        Get active user by their callsign excluding creators.

        Args:
            callsign (str): Callsign of the user.

        Returns:
            User | None: User object or None if not found.
        """
        return await User.filter(callsign=callsign, active=True, role__not=UserRole.CREATOR).first()

    @staticmethod
    async def create_user(
            telegram_id: int,
            callsign: str,
            role: UserRole = UserRole.USER,
            first_name: str | None = None,
            last_name: str | None = None,
            username: str | None = None,
    ) -> User:
        """
        Creates a new user.

        Args:
            telegram_id (int): Telegram ID of the user.
            callsign (str): Callsign of the user.
            role (UserRole, optional): Role of the user (USER, ADMIN, CREATOR). Defaults to USER.
            first_name (str, optional): First name of the user. Defaults to None.
            last_name (str, optional): Last name of the user. Defaults to None.
            username (str, optional): Username of the user. Defaults to None.
        
        Returns:
            User: The created User object.
        """

        user: User = await User.create(
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

        Args:
            user_telegram_id (int): Telegram ID of the user to update.
            **data: Arbitrary keyword arguments representing the fields to update.

        Returns:
            User: The updated User object.
        """
        user: User = await User.get(telegram_id=user_telegram_id)
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

        Args:
            telegram_id (int): Telegram ID of the user.
            new_role (UserRole): New role to assign to the user.

        Returns:
            bool: True if the role was successfully set, otherwise False.
        """
        user: User | None = await self.get_user_by_telegram_id(telegram_id=telegram_id)
        if not user:
            return False

        user.role = new_role
        user.updated_at = datetime.now(tz=settings.timezone_zoneinfo)
        await user.save()

        return True

    @staticmethod
    async def activate_user(telegram_id: int) -> bool:
        """
        Activates a user.

        Args:
            telegram_id (int): Telegram ID of the user to activate.

        Returns:
            bool: True if the user was successfully activated, otherwise False.
        """
        user: User | None = await User.filter(telegram_id=telegram_id, active=False).first()
        if not user:
            return False

        user.active = True
        user.updated_at = datetime.now(tz=settings.timezone_zoneinfo)
        await user.save()

        return True

    @staticmethod
    async def deactivate_user(telegram_id: int) -> bool:
        """
        Deactivates a user.

        Args:
            telegram_id (int): Telegram ID of the user to deactivate.

        Returns:
            bool: True if the user was successfully deactivated, otherwise False.
        """
        user: User | None = await User.filter(telegram_id=telegram_id, active=True).first()
        if not user:
            return False

        user.active = False
        user.updated_at = datetime.now(tz=settings.timezone_zoneinfo)
        await user.save()

        return True

    @staticmethod
    async def get_users_by_role(
            role: UserRole
    ) -> list[User]:
        """
        Get a list of active users by their role.

        Args:
            role (UserRole): Role of the users to retrieve.
        
        Returns:
            list[User]: List of active users with the specified role.
        """
        return await User.filter(role=role, active=True).all()

    @staticmethod
    async def get_users_without_reservation_exclude_creators() -> list[User]:
        """
        Get a list of active users without reservations.
        Creators are excluded from this list.

        Returns:
            list[User]: List of active users without reservations (excluding creators).
        """
        return await User.filter(reserved=False, active=True, role__not=UserRole.CREATOR).all()
