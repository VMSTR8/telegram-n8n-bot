from datetime import datetime

from pydantic import BaseModel, field_validator


class NewFormDataSchema(BaseModel):
    """
    Schema for new form data received from n8n.
    """
    id: int
    google_form_id: str
    title: str
    form_url: str
    created_at: datetime
    ended_at: datetime
    expired: bool = False

    @field_validator('created_at', 'ended_at', mode='before')
    @classmethod
    def parse_datetime(cls, value):
        """Parse ISO datetime strings to datetime objects."""
        if isinstance(value, str):
            # Handle ISO format with 'Z' suffix
            if value.endswith('Z'):
                value = value[:-1] + '+00:00'
            return datetime.fromisoformat(value)
        return value

    model_config = {
        "json_schema_extra": {
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
    }


NewFormSchema = NewFormDataSchema
