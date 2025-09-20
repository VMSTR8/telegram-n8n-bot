from datetime import datetime
from pydantic import BaseModel


class SurveySchema(BaseModel):
    """
    Схема Google формы опроса
    """
    id: int
    google_form_id: str
    title: str
    description: str | None = None
    form_url: str
    is_sent: bool
    created_at: datetime
    ended_at: datetime | None = None

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "google_form_id": "1FAIpQLSfD2...",
                "title": "Опрос удовлетворенности",
                "description": "Пожалуйста, заполните этот опрос.",
                "form_url": "https://docs.google.com/forms/d/e/1FAIpQLSfD2.../viewform",
                "is_sent": True,
                "created_at": "2023-01-01T12:00:00",
                "ended_at": "2023-01-31T12:00:00"
            }
        }
