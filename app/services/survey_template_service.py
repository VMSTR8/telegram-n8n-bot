from typing import List, Optional

from app.models import SurveyTemplate


class SurveyTemplateService:
    """
    Service for managing survey templates.
    """

    @staticmethod
    async def create_survey_template(
            name: str,
            json_content: dict
    ) -> SurveyTemplate:
        """
        Creates a new survey template.

        :param name: Name of the survey template
        :param json_content: JSON content of the survey template
        :return: SurveyTemplate - created SurveyTemplate object
        """
        return await SurveyTemplate.create(
            name=name,
            json_content=json_content
        )
    
    @staticmethod
    async def get_survey_template_by_name(
        name: str
    ) -> Optional[SurveyTemplate]:
        """
        Gets a survey template by its name.

        :param name: Name of the survey template
        :return: Optional[SurveyTemplate] - SurveyTemplate object or None if not found
        """
        return await SurveyTemplate.filter(name=name).first()
