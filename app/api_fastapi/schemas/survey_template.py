from pydantic import BaseModel


class SurveyTemplateSchema(BaseModel):
    """
    Schema for survey template data.
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
