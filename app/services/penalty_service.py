from typing import List, Dict
from datetime import datetime

from tortoise.functions import Count

from app.models import Penalty, User
from config.settings import settings


class PenaltyService:
    """
    Сервис для работы со штрафными баллами пользователей
    """
    @staticmethod
    async def add_penalty(
            user: int,
            survey: int,
            reason: str,
            penalty_date: datetime = datetime.now(tz=settings.timezone_zoneinfo),
    ) -> Penalty:
        """
        Добавляет новый штрафной балл пользователю.

        :param user: id пользователя
        :param survey: id опроса
        :param reason: Причина назначения штрафного балла
        :param penalty_date: Дата и время назначения штрафного балла (по умолчанию текущее время)
        :return: Объект Penalty
        """
        pass

    @staticmethod
    async def get_user_penalties(
            user: User
    ) -> List[Penalty]:
        """
        Получает все штрафные баллы пользователя.

        :param user: Пользователь (User)
        :return: list[Penalty] - Список штрафных баллов пользователя
        """
        query = Penalty.filter(user=user)
        return await query.prefetch_related('survey').all()

    @staticmethod
    async def get_user_penalty_count(
            user: User
    ) -> int:
        """
        Получает количество штрафных баллов пользователя.

        :param user: Пользователь (User)
        :return: int - Количество штрафных баллов пользователя
        """
        return await Penalty.filter(user=user).count()

    @staticmethod
    async def get_all_users_with_three_penalties() -> List[Dict]:
        """
        Получает всех пользователей, у которых 3 и более штрафных баллов.

        :return: list[Dict] - Список пользователей с количеством штрафных баллов
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
        Удаляет все штрафные баллы из базы данных.
        
        :return: None
        """
        await Penalty.all().delete()
