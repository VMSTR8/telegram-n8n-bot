import logging
from functools import wraps
from typing import Callable, Awaitable, TypeVar

from fastapi import HTTPException, Request

from config import settings

logger = logging.getLogger(__name__)
T = TypeVar('T')


class FastAPIValidate:
    """
    A class containing decorators for validating FastAPI requests.

    Methods:
        validate_header_secret: Decorator to validate a specific header against a secret value.
    """

    @staticmethod
    def validate_header_secret(
            header_name: str = 'X-Telegram-Bot-Api-Secret-Token',
            secret: str | None = settings.telegram.webhook_secret,
            error_status_code: int = 403,
            error_detail: str = 'Forbidden'
    ) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
        """
        Decorator factory to validate a specific header against a secret value.

        Args:
            header_name: The name of the header to validate.
            secret: The expected secret value to compare against.
            error_status_code: The HTTP status code to return on validation failure.
            error_detail: The detail message to return on validation failure.
        
        Returns:
            A decorator that can be applied to FastAPI route handler functions.
        """

        def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
            """
            The actual decorator function.
            
            Args:
                func: The function to be decorated.
            
            Returns:
                The wrapped asynchronous function with the same arguments as the original function.
            """

            @wraps(func)
            async def wrapper(*args, request: Request, **kwargs) -> T:
                secret_header: str | None = request.headers.get(header_name)

                if not secret or not secret_header:
                    logger.error('Webhook signature validation failed: missing header or secret %s', header_name)
                    raise HTTPException(status_code=error_status_code, detail=error_detail)

                normalized_header: str = str(secret_header).strip()
                normalized_secret: str = str(secret).strip()

                if len(normalized_header) < 1 or len(normalized_secret) < 1:
                    logger.error('Webhook signature validation failed: empty header or secret for %s', header_name)
                    raise HTTPException(status_code=error_status_code, detail=error_detail)

                if normalized_secret != normalized_header:
                    logger.error('Webhook signature validation failed: invalid signature for header %s', header_name)
                    raise HTTPException(status_code=error_status_code, detail=error_detail)

                return await func(*args, request=request, **kwargs)

            return wrapper

        return decorator
