from typing import List
from pydantic import BaseModel


class SurveyAnswerSchema(BaseModel):
    """
    Schema for survey answer data.
    """
    answer: str

    class Config:
        schema_extra = {
            "example": {
                "answer": "drinkins"
            }
        }


class SurveyResponseSchema(BaseModel):
    """
    Schema for survey response data from n8n.
    """
    google_form_id: str
    answers: List[SurveyAnswerSchema]

    class Config:
        schema_extra = {
            "example": {
                "google_form_id": "1FAIpQLSfD2...",
                "answers": [
                    {"answer": "drinkins"},
                    {"answer": "siuuuuuu"},
                    {"answer": "ultrakiller"}
                ]
            }
        }
