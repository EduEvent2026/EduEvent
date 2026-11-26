import datetime as dt
import re
from abc import ABC, abstractmethod
from .client import EventsApiError
from .models import CalendarView, ViewType
from .service import CalendarService
from fastapi import APIRouter, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

class InvalidDateError(ValueError):
    """Data z żądania ma zły format albo nie istnieje."""
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message

class ICalendarAPI(ABC):
    """Publiczne API modułu 5 (REST/JSON)."""

    @abstractmethod
    def get_day(self, target_date: str) -> CalendarView: ...

    @abstractmethod
    def get_week(self, target_date: str) -> CalendarView: ...

    @abstractmethod
    def get_month(self, target_date: str) -> CalendarView: ...


class CalendarController(ICalendarAPI):
    """Odbiera żądanie HTTP, sprawdza poprawność daty, wywołuje serwis i zwraca widok."""

    def __init__(self, service: CalendarService):
        self._service = service

    def get_day(self, target_date: str) -> CalendarView:
        return self._service.build_view(ViewType.DAY, self._parse_date(target_date))

    def get_week(self, target_date: str) -> CalendarView:
        return self._service.build_view(ViewType.WEEK, self._parse_date(target_date))

    def get_month(self, target_date: str) -> CalendarView:
        return self._service.build_view(ViewType.MONTH, self._parse_date(target_date))

    @staticmethod
    def _parse_date(raw_date: str) -> dt.date:
        if raw_date is None or raw_date == "":
            raise InvalidDateError("DATE_REQUIRED","Parametr date jest wymagany (format RRRR-MM-DD)")
        if not _DATE_RE.match(raw_date):
            raise InvalidDateError("DATE_INVALID_FORMAT","Data musi mieć format RRRR-MM-DD, np. 2026-11-24.")
        try:
            value = dt.date.fromisoformat(raw_date)
        except ValueError:
            raise InvalidDateError("DATE_NOT_EXISTS",f"Data {raw_date} nie istnieje w kalendarzu.")
        return value

def _error_response(status: int, code: str, message: str) -> JSONResponse:
    """Każdy błąd ma ten sam kształt, czyli: {"error": {"code": ..., "message": ...}}."""
    return JSONResponse(
        status_code=status,
        content={"error": {"code": code, "message": message}},
    )

def create_calendar_router(controller: CalendarController) -> APIRouter:
    """Endpointy REST modułu 5. Kontroler zwraca CalendarView, tutaj zminana na JSON."""
    router = APIRouter(prefix="/api/calendar", tags=["calendar"])

    # GET /api/calendar/day?date=2026-11-24
    @router.get("/day")
    def get_day(date: str | None = None):
        return controller.get_day(date).to_json()

    # GET /api/calendar/week?date=2026-11-24
    @router.get("/week")
    def get_week(date: str | None = None):
        return controller.get_week(date).to_json()

    # GET /api/calendar/month?date=2026-11-24
    @router.get("/month")
    def get_month(date: str | None = None):
        return controller.get_month(date).to_json()

    return router

def register_error_handlers(app: FastAPI) -> None:
    """Zmiana wszystkich błędów na jeden format."""

    @app.exception_handler(InvalidDateError)
    async def handle_invalid_date(request: Request, error: InvalidDateError):
        return _error_response(400, error.code, error.message)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, error: RequestValidationError):
        return _error_response(400, "VALIDATION_ERROR", "Niepoprawne dane wejściowe.")

    @app.exception_handler(EventsApiError)
    async def handle_events_api_error(request: Request, error: EventsApiError):
        return _error_response(500, "EVENTS_UNAVAILABLE", "Moduł wydarzeń jest niedostępny.")

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(request: Request, error: StarletteHTTPException):
        if error.status_code == 404:
            return _error_response(404, "NOT_FOUND", "Nie znaleziono zasobu.")
        return _error_response(error.status_code, f"HTTP_{error.status_code}", "Błąd żądania.")

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, error: Exception):
        return _error_response(500, "INTERNAL_ERROR", "Wewnętrzny błąd serwera.")