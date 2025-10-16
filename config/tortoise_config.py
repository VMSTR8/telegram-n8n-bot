"""
Tortoise ORM configuration.
"""
from config import settings

TORTOISE_ORM: dict = {
    "connections": {
        "default": settings.database.url,
    },
    "apps": {
        "models": {
            "models": ["app.models", "aerich.models"],
            "default_connection": "default",
        },
    },
}
