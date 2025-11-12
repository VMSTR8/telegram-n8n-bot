from pydantic import BaseModel


class RecaptchaResponseSchema(BaseModel):
    """
    Schema for reCAPTCHA verification response.
    """
    status: str
    message: str
    score: float | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "ok",
                "message": "reCAPTCHA verification successful.",
                "score": 0.9
            }
        }
    }
