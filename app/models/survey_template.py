from tortoise.models import Model
from tortoise import fields


class SurveyTemplate(Model):
    """
    Model representing a survey template.
    """
    id = fields.IntField(primary_key=True, description='Primary key')
    name = fields.CharField(max_length=255, unique=True, description='Name of the survey template')
    json_content = fields.JSONField(description='JSON content of the survey template')

    class Meta:
        table = 'survey_templates'
        table_description = 'Survey templates stored in JSON format'

    def __str__(self) -> str:
        return f'Survey template: {self.name} (ID: {self.id})'
