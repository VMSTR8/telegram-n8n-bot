from datetime import datetime
from pydantic import BaseModel


class PenaltySchema(BaseModel):
    """
    Схема для штрафов пользователей за неучастие в опросах.
    """
    id: int
    user: int
    survey: int
    reason: str
    penalty_date: datetime

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "user": 123,
                "survey": 456,
                "reason": "Неучастие в опросе",
                "penalty_date": "2023-10-01T12:34:56"
            }
        }
