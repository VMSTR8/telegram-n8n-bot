from pydantic import BaseModel


class SurveyInfo(BaseModel):
    """Schema for the nested info object in survey data."""
    title: str
    documentTitle: str


class SurveyData(BaseModel):
    """Schema for survey data sent to n8n."""
    info: SurveyInfo
