from app.models import SurveyTemplate


class SurveyTemplateService:
    """
    Service for managing survey templates.

    Methods:
        create_survey_template: Creates a new survey template.
        get_survey_template_by_name: Retrieves a survey template by its name.
    """

    @staticmethod
    async def create_survey_template(
            name: str,
            json_content: dict
    ) -> SurveyTemplate:
        """
        Creates a new survey template.

        Args:
            name (str): Name of the survey template
            json_content (dict): JSON content of the survey template
        
        Returns:
            SurveyTemplate: The created SurveyTemplate object
        """
        return await SurveyTemplate.create(
            name=name,
            json_content=json_content
        )

    @staticmethod
    async def get_survey_template_by_name(
            name: str
    ) -> SurveyTemplate | None:
        """
        Gets a survey template by its name.

        Args:
            name (str): Name of the survey template

        Returns:
            SurveyTemplate | None: SurveyTemplate object if found, else None
        """
        return await SurveyTemplate.filter(name=name).first()
