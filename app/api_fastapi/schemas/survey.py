from datetime import datetime
from pydantic import BaseModel


class SurveySchema(BaseModel):
    """
    Schema for survey data.
    """
    id: int
    google_form_id: str
    title: str
    form_url: str
    created_at: datetime = datetime.now()
    ended_at: datetime = None
    expired: bool = False

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "google_form_id": "1FAIpQLSfD2...",
                "title": "Survey on User Satisfaction",
                "form_url": "https://docs.google.com/forms/d/e/1FAIpQLSfD2.../viewform",
                "created_at": "2023-01-01T12:00:00",
                "ended_at": "2023-01-31T12:00:00",
                "expired": False
            }
        }
