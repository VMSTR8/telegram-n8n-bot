from pydantic import BaseModel

class SubmitFormSchema(BaseModel):
    """
    Schema for form submission.
    """
    name: str
    age: int
    contactType: str
    telegram: str | None = None
    phone: str | None = None
    experience: str
    recaptchaToken: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "John Doe",
                "age": 30,
                "telegram": "@johndoe",
                "phone": None,
                "contactType": "telegram",
                "experience": "yes",
                "recaptchaToken": "03AGdBq24..."
            }
        }
    }
