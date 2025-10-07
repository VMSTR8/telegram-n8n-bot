from typing import List
from datetime import datetime
from pydantic import BaseModel



class NewFormDataSchema(BaseModel):
    """
    Schema for new form data received from n8n.
    """
    id: int
    google_form_id: str
    title: str
    form_url: str
    created_at: str
    ended_at: str
    expired: bool = False

    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "google_form_id": "1FAIpQLSfD2...",
                "title": "Govnomes na prirode 2077",
                "form_url": "https://docs.google.com/forms/d/e/1FAIpQLSfD2.../viewform",
                "created_at": "2025-01-01T12:00:00",
                "ended_at": "2025-01-31T12:00:00",
                "expired": False
            }
        }


class NewFormListSchema(BaseModel):
    """
    Schema for a list of new forms.
    """
    data: List[NewFormDataSchema]

    class Config:
        schema_extra = {
            "example": {
                "data": [
                    {
                        "id": 1,
                        "google_form_id": "1FAIpQLSfD2...",
                        "title": "Govnomes na prirode 2077",
                        "form_url": "https://docs.google.com/forms/d/e/1FAIpQLSfD2.../viewform",
                        "created_at": "2025-01-01T12:00:00",
                        "ended_at": "2025-01-31T12:00:00",
                        "expired": False
                    }
                ]
            }
        }
