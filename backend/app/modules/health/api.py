from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.config import Settings, get_settings
from app.core.errors import AppError, ErrorResponse

router = APIRouter(prefix="/api/v1/health", tags=["System"])


class LiveResponse(BaseModel):
    status: str
    service: str


class ReadyResponse(BaseModel):
    status: str
    knowledge_index: str
    llm: str


@router.get("/live", response_model=LiveResponse, summary="Проверка процесса")
async def live(settings: Annotated[Settings, Depends(get_settings)]) -> LiveResponse:
    return LiveResponse(status="alive", service=settings.app_name)


@router.get(
    "/ready",
    response_model=ReadyResponse,
    responses={503: {"model": ErrorResponse, "description": "Зависимости ещё не готовы"}},
    summary="Проверка готовности к ответам",
)
async def ready() -> ReadyResponse:
    raise AppError(503, "SERVICE_NOT_READY", "Knowledge index and LLM are not configured")
