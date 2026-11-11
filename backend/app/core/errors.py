from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


class ErrorBody(BaseModel):
    code: str
    message: str
    request_id: str
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: ErrorBody


class AppError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    request_id = str(request.state.request_id)
    body = ErrorResponse(
        error=ErrorBody(code=exc.code, message=exc.message, request_id=request_id)
    )
    return JSONResponse(status_code=exc.status_code, content=body.model_dump())
