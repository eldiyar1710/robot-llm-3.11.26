from typing import Literal
from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.errors import AppError, ErrorResponse

router = APIRouter(prefix="/api/v1/dialog", tags=["Dialog"])


class TextQuestion(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    language: Literal["kk", "ru", "en"] | None = None
    session_id: UUID | None = None
    idempotency_key: str | None = Field(default=None, min_length=1, max_length=128)


class SourceReference(BaseModel):
    document_id: UUID
    version_id: UUID
    source_path: str
    source_url: str
    page_start: int = Field(ge=1)
    page_end: int = Field(ge=1)


class TextAnswer(BaseModel):
    turn_id: UUID
    answer: str
    language: Literal["kk", "ru", "en"]
    grounded: bool
    sources: list[SourceReference]


@router.post(
    "/text",
    response_model=TextAnswer,
    responses={503: {"model": ErrorResponse, "description": "База знаний ещё не подключена"}},
    summary="Задать текстовый вопрос",
    description="Контракт доступен; обработка вопросов включается после индексации и RAG.",
)
async def ask_text(_question: TextQuestion) -> TextAnswer:
    raise AppError(503, "KNOWLEDGE_NOT_READY", "Knowledge index is not configured")
