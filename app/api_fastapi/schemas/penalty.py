from datetime import datetime
from pydantic import BaseModel


class PenaltySchema(BaseModel):
    """
    Schema for representing a penalty assigned to a user for survey-related infractions.
    """
    id: int
    user: int
    survey: int
    reason: str
    penalty_date: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "user": 123,
                "survey": 456,
                "reason": "Late submission",
                "penalty_date": "2023-10-01T12:34:56"
            }
        }
