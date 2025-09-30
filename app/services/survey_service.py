from datetime import datetime
from typing import Optional, List

from app.models import Survey
from config import settings


class SurveyService:
    """
    Service for managing surveys.
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
        Creates a new survey.

        :param google_form_id: Google form ID
        :param title: Survey title
        :param form_url: Google form URL
        :param ended_at: Date and time when the survey ends
        :param description: Survey description (optional)
        :return: Survey - created Survey object
        """
        pass

    @staticmethod
    async def get_survey_by_google_form_id(
            google_form_id: str
    ) -> Optional[Survey]:
        """
        Gets a survey by its Google form ID.

        :param google_form_id: Google form ID
        :return: Optional[Survey] - Survey object or None if not found
        """
        return await Survey.filter(google_form_id=google_form_id).first()

    async def get_active_surveys(self) -> List[Survey]:
        """
        Gets all active surveys (not finished).

        :return: List[Survey] - List of active surveys
        """
        return await Survey.filter(ended_at__gt=datetime.now(tz=self.tz)).all()
