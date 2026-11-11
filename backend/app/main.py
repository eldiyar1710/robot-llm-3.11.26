import json
import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response

from app.core.config import get_settings
from app.core.errors import AppError, ErrorBody, ErrorResponse, app_error_handler
from app.modules.dialog.api import router as dialog_router
from app.modules.health.api import router as health_router

logger = logging.getLogger(__name__)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return json.dumps(
            {"level": record.levelname, "logger": record.name, "message": record.getMessage()},
            ensure_ascii=False,
        )


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(level=settings.log_level, handlers=[handler])
    logger.info("service_started")
    yield
    logger.info("service_stopped")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description=(
            "University AI assistant API. "
            "Knowledge and robot adapters are not configured yet."
        ),
        lifespan=lifespan,
    )

    @app.middleware("http")
    async def request_id_middleware(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # Starlette generates the ID; caller-supplied values are not trusted as log identifiers.
        request.state.request_id = uuid4()
        response = await call_next(request)
        response.headers["X-Request-ID"] = str(request.state.request_id)
        return response

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        return await app_error_handler(request, exc)

    @app.exception_handler(RequestValidationError)
    async def handle_validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [{"loc": list(error["loc"]), "msg": error["msg"]} for error in exc.errors()]
        body = ErrorResponse(
            error=ErrorBody(
                code="VALIDATION_ERROR",
                message="Request validation failed",
                request_id=str(request.state.request_id),
                details={"errors": errors},
            )
        )
        return JSONResponse(status_code=422, content=body.model_dump())

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        body = ErrorResponse(
            error=ErrorBody(
                code="NOT_FOUND" if exc.status_code == 404 else "HTTP_ERROR",
                message=str(exc.detail),
                request_id=str(request.state.request_id),
            )
        )
        return JSONResponse(status_code=exc.status_code, content=body.model_dump())

    app.include_router(health_router)
    app.include_router(dialog_router)
    return app


app = create_app()
