from datetime import datetime
from typing import Any

from tortoise.functions import Count
from tortoise.queryset import QuerySet

from app.models import Penalty, User
from config.settings import settings


class PenaltyService:
    """
    Service class for managing user penalties.

    Methods:
        add_penalty: Adds a new penalty point to a user.
        get_user_penalties: Retrieves all penalty points for a user.
        get_user_penalty_count: Gets the number of penalty points for a user.
        get_all_users_with_three_penalties: Retrieves all users with 3 or more penalty points.
        delete_user_penalties: Deletes all penalty points for a specific user.
        delete_all_penalties: Deletes all penalty points from the database.
    """

    @staticmethod
    async def add_penalty(
            user_id: int,
            survey_id: int,
            reason: str,
            penalty_date: datetime = datetime.now(
                tz=settings.timezone_zoneinfo
            ),
    ) -> Penalty:
        """
        Adds a new penalty point to the user.

        Args:
            user_id (int): Telegram ID of the user.
            survey_id (int): ID of the survey associated with the penalty.
            reason (str): Reason for the penalty.
            penalty_date (datetime, optional): Date and time of the penalty. Defaults to current date and time.
        
        Returns:
            Penalty: The created Penalty object.
        """
        penalty: Penalty = Penalty(
            user_id=user_id,
            survey_id=survey_id,
            reason=reason,
            penalty_date=penalty_date
        )
        await penalty.save()
        return penalty

    @staticmethod
    async def get_user_penalties(
            user: User
    ) -> list[Penalty]:
        """
        Gets all penalty points of a user.

        Args:
            user (User): User object
        
        Returns:
            list[Penalty]: List of Penalty objects for the user
        """
        query: QuerySet[Penalty] = Penalty.filter(user=user)
        return await query.prefetch_related('survey').all()

    @staticmethod
    async def get_user_penalty_count(
            user: User
    ) -> int:
        """
        Gets the number of penalty points for a user.

        Args:
            user (User): User object
        
        Returns:
            int: Number of penalty points for the user
        """
        return await Penalty.filter(user=user).count()

    @staticmethod
    async def get_all_users_with_three_penalties() -> list[dict[str, Any]]:
        """
        Gets all users with 3 or more penalty points.

        Returns:
            list[dict[str, Any]]: List of dictionaries containing user info and penalty count
        """
        users: list[dict[str, Any]] = await User.annotate(
            penalty_count=Count('penalties')
        ).filter(penalty_count__gte=3).all().values(
            'telegram_id', 'username', 'callsign', 'penalty_count'
        )
        return users

    @staticmethod
    async def delete_user_penalties(user: User) -> None:
        """
        Deletes all penalty points for a specific user.

        Args:
            user (User): User object whose penalties are to be deleted
        
        Returns:
            None: All penalty points for the user are deleted
        """
        await Penalty.filter(user=user).delete()

    @staticmethod
    async def delete_all_penalties() -> None:
        """
        Deletes all penalty points from the database.

        Returns:
            None: All penalty points are deleted
        """
        await Penalty.all().delete()
