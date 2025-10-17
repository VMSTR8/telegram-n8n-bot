from pydantic import BaseModel


class SurveyTemplateSchema(BaseModel):
    """
    Schema for survey template data.

    Attributes:
        id (int): Internal database ID of the survey template
        name (str): Name of the survey template
        json_content (dict): JSON content of the survey template
    """
    id: int
    name: str
    json_content: dict

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Google Forms template",
                "json_content":
                    {
                        "info": {
                            "title": "{{title}}",
                            "documentTitle": "{{ended_at}}"
                        }
                    }
            }
        }
