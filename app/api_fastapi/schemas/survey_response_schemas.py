from pydantic import BaseModel


class SurveyAnswerSchema(BaseModel):
    """
    Schema for survey answer data.

    Attributes:
        answer (str): The answer provided in the survey.
    """
    answer: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "answer": "drinkins"
            }
        }
    }


class SurveyResponseSchema(BaseModel):
    """
    Schema for survey response data from n8n.

    Attributes:
        google_form_id (str): The Google Form ID associated with the survey.
        answers (list[SurveyAnswerSchema]): A list of answers provided in the survey.
    """
    google_form_id: str
    answers: list[SurveyAnswerSchema]

    model_config = {
        "json_schema_extra": {
            "example": {
                "google_form_id": "1FAIpQLSfD2...",
                "answers": [
                    {"answer": "drinkins"},
                    {"answer": "siuuuuuu"},
                    {"answer": "ultrakiller"}
                ]
            }
        }
    }
