from datetime import datetime
from pydantic import BaseModel


class SurveySchema(BaseModel):
    """
    Schema for survey data.

    Attributes:
        id (int): Internal database ID of the survey
        google_form_id (str): Google Form ID associated with the survey
        title (str): Title of the survey
        form_url (str): URL of the Google Form
        created_at (datetime): Timestamp when the survey was created
        ended_at (datetime | None): Timestamp when the survey ended
        expired (bool): Indicates if the survey has expired
    """
    id: int
    google_form_id: str
    title: str
    form_url: str
    created_at: datetime = datetime.now()
    ended_at: datetime = None
    expired: bool = False

    class Config:
        from_attributes = True
        json_schema_extra = {
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
