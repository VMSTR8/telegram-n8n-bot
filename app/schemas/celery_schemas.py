from pydantic import BaseModel
from typing import Any


class TaskResponse(BaseModel):
    """Schema for general Celery task response (success/error)."""
    status: str
    message_id: int | None = None
    message: str | None = None
    detail: str | None = None


class QueueResult(BaseModel):
    """Schema for message queue result."""
    status: str
    task_id: str | None = None
    chat_id: int | None = None
    message: str | None = None
    message_count: int | None = None


class TaskStatus(BaseModel):
    """Schema for checking the status of a Celery task."""
    task_id: str
    status: str
    result: Any | None = None
    message: str | None = None
