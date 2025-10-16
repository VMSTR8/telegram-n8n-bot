from datetime import datetime
from zoneinfo import ZoneInfo

from app.models import Survey
from config import settings


class SurveyService:
    """
    Service for managing surveys.

    Attributes:
        tz (ZoneInfo): Timezone information from settings
    
    Methods:
        get_survey_by_google_form_id: Retrieves a survey by its Google form ID.
        get_active_surveys: Retrieves all active (not finished) surveys.
    """

    def __init__(self):
        self.tz: ZoneInfo = settings.timezone_zoneinfo

    @staticmethod
    async def get_survey_by_google_form_id(
            google_form_id: str
    ) -> Survey | None:
        """
        Gets a survey by its Google form ID.

        Args:
            google_form_id (str): Google form ID of the survey.
        
        Returns:
            Survey | None: Survey object if found, else None
        """
        return await Survey.filter(google_form_id=google_form_id).first()

    async def get_active_surveys(self) -> list[Survey]:
        """
        Gets all active surveys (not finished).

        Returns:
            list[Survey]: List of active Survey objects
        """
        return await Survey.filter(ended_at__gt=datetime.now(tz=self.tz)).all()
