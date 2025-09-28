from tortoise.models import Model
from tortoise import fields


class Penalty(Model):
    """
    Model representing a penalty point assigned to a user for not participating in surveys.
    """
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField(
        'models.User',
        related_name='penalties',
        description='User to whom the penalty point is assigned'
    )
    survey = fields.ForeignKeyField(
        'models.Survey',
        related_name='penalties',
        description='Survey for which the penalty point is assigned'
    )
    reason = fields.TextField(description='Reason for assigning the penalty point')
    penalty_date = fields.DatetimeField(auto_now_add=True, description='Date and time of penalty point assignment')

    class Meta:
        table = 'penalties'
        table_description = 'User penalty points for not participating in surveys'

    def __str__(self) -> str:
        """String representation of the penalty point"""
        return f'Penalty {self.id} for User {self.user} in Survey {self.survey}'
