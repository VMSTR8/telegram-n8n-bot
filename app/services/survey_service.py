from typing import Optional, List
from datetime import datetime

from app.models import Survey
from config import settings


class SurveyService:
    """
    Сервис для работы с опросами Google Forms
    """
    def __init__(self):
        self.tz = settings.timezone_zoneinfo

    @staticmethod
    async def create_survey(
            google_form_id: str,
            title: str,
            form_url: str,
            ended_at: datetime,
            description: Optional[str] = None,
    ) -> Survey:
        """
        Создает новый опрос.

        :param google_form_id: ID Google формы
        :param title: Название опроса
        :param form_url: URL Google формы
        :param ended_at: Дата и время завершения опроса
        :param description: Описание опроса
        :return: Объект Survey
        """
        pass

    @staticmethod
    async def get_survey_by_google_form_id(
            google_form_id: str
    ) -> Optional[Survey]:
        """
        Получает опрос по ID Google формы.

        :param google_form_id: ID Google формы
        :return: Объект Survey или None, если не найден
        """
        return await Survey.filter(google_form_id=google_form_id).first()

    async def get_active_surveys(self) -> List[Survey]:
        """
        Получает все активные опросы (не завершенные).

        :return: Список объектов Survey
        """
        return await Survey.filter(ended_at__gt=datetime.now(tz=self.tz)).all()
