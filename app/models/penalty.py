from tortoise.models import Model
from tortoise import fields


class Penalty(Model):

    id = fields.IntField(pk=True)
    user_id = fields.ForeignKeyField(
        'models.User',
        related_name='penalties',
        description='Пользователь, которому назначен штрафной балл'
    )
    survey_id = fields.ForeignKeyField(
        'models.Survey',
        related_name='penalties',
        description='Опрос, за который назначен штрафной балл'
    )
    reason = fields.TextField(description='Причина назначения штрафного балла')
    penalty_date = fields.DatetimeField(auto_now_add=True, description='Дата и время назначения штрафного балла')

    class Meta:
        table = 'penalties'
        table_description = 'Штрафные баллы пользователей за неучастие в опросах'

    def __str__(self) -> str:
        """Строковое представление штрафного балла"""
        return f'Penalty {self.id} for User {self.user_id} in Survey {self.survey_id}'
