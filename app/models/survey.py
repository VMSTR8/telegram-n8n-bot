from tortoise.models import Model
from tortoise import fields


class Survey(Model):
    """
    Model representing a Google Forms survey.
    """
    id = fields.IntField(pk=True)
    google_form_id = fields.CharField(max_length=255, unique=True, description='Google Form ID')
    title = fields.CharField(max_length=255, description='Survey title')
    description = fields.TextField(null=True, description='Survey description')
    form_url = fields.CharField(max_length=512, description='Google Form URL')

    is_sent = fields.BooleanField(default=False, description='Send status to users')
    created_at = fields.DatetimeField(auto_now_add=True, description='Date and time of survey creation')
    ended_at = fields.DatetimeField(description='Date and time of survey completion')

    class Meta:
        table = "surveys"
        table_description = "Google Forms surveys"

    def __str__(self) -> str:
        """String representation of the survey"""
        return f'Survey {self.title}: {self.form_url}'

    @property
    def is_notified(self) -> bool:
        """Checks if the survey has been sent to users"""
        return self.is_sent
