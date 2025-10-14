import logging
from functools import wraps
from typing import Callable, Any, Optional, Awaitable

from fastapi import HTTPException, Request

from config import settings


class FastAPIValidate:
    """
    A class containing decorators for validating FastAPI requests.
    """

    @staticmethod
    def validate_header_secret(
            header_name: str = 'X-Telegram-Bot-Api-Secret-Token',
            secret: Optional[str] = settings.telegram.webhook_secret,
            error_status_code: int = 403,
            error_detail: str = 'Forbidden'
    ):
        """
        Decorator factory to validate a specific header against a secret value.

        :param header_name: str - the name of the header to validate.
        :param secret: Optional[str] - the secret value to compare against.
        :param error_status_code: int - HTTP status code to return on failure.
        :param error_detail: str - detail message for the HTTP exception.
        :return: Callable - the decorator function.
        """

        def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
            """
            The actual decorator function.
            
            :param func: Callable[..., Awaitable[Any]] - the function to decorate.
            :return: Callable[..., Awaitable[Any]] - the wrapped function.
            """

            @wraps(func)
            async def wrapper(*args, request: Request, **kwargs) -> Any:
                secret_header = request.headers.get(header_name)

                if not secret or not secret_header:
                    logging.error('Verifying webhook signature failed.')
                    raise HTTPException(status_code=error_status_code, detail=error_detail)

                normalized_header: str = str(secret_header).strip()
                normalized_secret: str = str(secret).strip()

                if len(normalized_header) < 1 or len(normalized_secret) < 1:
                    logging.error(
                        'Verifying webhook signature failed due to empty values.'
                    )
                    raise HTTPException(status_code=error_status_code, detail=error_detail)

                if normalized_secret != normalized_header:
                    logging.error('Invalid webhook signature received.')
                    raise HTTPException(status_code=error_status_code, detail=error_detail)

                return await func(*args, request=request, **kwargs)

            return wrapper

        return decorator
