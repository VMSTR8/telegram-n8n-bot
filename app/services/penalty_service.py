from typing import List, Dict
from datetime import datetime

from tortoise.functions import Count

from app.models import Penalty, User
from config.settings import settings


class PenaltyService:
    """
    Service class for managing user penalties.
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

        :param user_id: User id
        :param survey_id: Survey id
        :param reason: Reason for the penalty
        :param penalty_date: Date and time of the penalty (default: now)
        :return: Penalty - The created penalty point
        """
        penalty = Penalty(
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
    ) -> List[Penalty]:
        """
        Gets all penalty points of a user.

        :param user: User (User)
        :return: List[Penalty] - List of penalty points for the user
        """
        query = Penalty.filter(user=user)
        return await query.prefetch_related('survey').all()

    @staticmethod
    async def get_user_penalty_count(
            user: User
    ) -> int:
        """
        Gets the number of penalty points for a user.

        :param user: User (User)
        :return: int - Number of penalty points for the user
        """
        return await Penalty.filter(user=user).count()

    @staticmethod
    async def get_all_users_with_three_penalties() -> List[Dict]:
        """
        Gets all users with 3 or more penalty points.

        :return: List[Dict] - List of users with penalty points
        """
        users = await User.annotate(
            penalty_count=Count('penalties')
        ).filter(penalty_count__gte=3).all().values(
            'telegram_id', 'username', 'callsign', 'penalty_count'
        )
        return users

    @staticmethod
    async def delete_all_penalties() -> None:
        """
        Deletes all penalty points from the database.

        :return: None - All penalty points are deleted
        """
        await Penalty.all().delete()
