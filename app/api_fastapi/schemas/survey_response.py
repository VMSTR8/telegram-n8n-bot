from typing import List

from pydantic import BaseModel


class SurveyAnswerSchema(BaseModel):
    """
    Schema for survey answer data.

    Attributes:
        answer (str): The answer provided in the survey.
    """
    answer: str

    class Config:
        json_schema_extra = {
            "example": {
                "answer": "drinkins"
            }
        }


class SurveyResponseSchema(BaseModel):
    """
    Schema for survey response data from n8n.

    Attributes:
        google_form_id (str): The Google Form ID associated with the survey.
        answers (List[SurveyAnswerSchema]): List of answers provided in the survey.
    """
    google_form_id: str
    answers: List[SurveyAnswerSchema]

    class Config:
        json_schema_extra = {
            "example": {
                "google_form_id": "1FAIpQLSfD2...",
                "answers": [
                    {"answer": "drinkins"},
                    {"answer": "siuuuuuu"},
                    {"answer": "ultrakiller"}
                ]
            }
        }
