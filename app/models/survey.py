from tortoise.models import Model
from tortoise import fields


class Survey(Model):
    """
    Модель опроса Google Forms
    """
    id = fields.IntField(pk=True)
    google_form_id = fields.CharField(max_length=255, unique=True, description='ID Google формы')
    title = fields.CharField(max_length=255, description='Название опроса')
    description = fields.TextField(null=True, description='Описание опроса')
    form_url = fields.CharField(max_length=512, description='URL Google')

    is_sent = fields.BooleanField(default=False, description='Отправлен ли опрос пользователям')
    created_at = fields.DatetimeField(auto_now_add=True, description='Дата и время создания записи')
    ended_at = fields.DatetimeField(null=True, description='Дата и время завершения опроса')

    class Meta:
        table = "surveys"
        table_description = "Опросы Google Forms"

    def __str__(self) -> str:
        """Строковое представление опроса"""
        return f'Survey {self.title}: {self.form_url}'

    @property
    def is_notified(self) -> bool:
        """Проверяет, был ли опрос отправлен пользователям"""
        return self.is_sent
