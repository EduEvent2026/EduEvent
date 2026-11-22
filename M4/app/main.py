from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.database import init_db
from app.exceptions import AppException
from app.router import router as registrations_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    lifespan=lifespan,
)


def _error_json(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
    )


@app.exception_handler(AppException)
async def app_exception_handler(_: Request, exc: AppException) -> JSONResponse:
    return _error_json(exc.status_code, exc.code, exc.message)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _: Request, exc: RequestValidationError
) -> JSONResponse:
    # Zasady HTTP API wymagają kodu 400
    first_error = exc.errors()[0] if exc.errors() else {}
    location = ".".join(str(p) for p in first_error.get("loc", [])[1:])
    detail = first_error.get("msg", "Nieprawidłowe dane wejściowe")
    message = f"Błędne pole '{location}': {detail}" if location else detail
    return _error_json(
        status_code=status.HTTP_400_BAD_REQUEST,
        code="VALIDATION_ERROR",
        message=message,
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    _: Request, exc: StarletteHTTPException
) -> JSONResponse:
    code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
    }
    return _error_json(
        status_code=exc.status_code,
        code=code_map.get(exc.status_code, "HTTP_ERROR"),
        message=str(exc.detail),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    # Logujemy szczegóły po stronie serwera, nigdy nie zwracamy stack trace'a klientowi
    logger.exception("Nieobsłużony błąd serwera: %s", exc)
    return _error_json(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="INTERNAL_SERVER_ERROR",
        message="Wystąpił wewnętrzny błąd serwera",
    )


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(registrations_router)