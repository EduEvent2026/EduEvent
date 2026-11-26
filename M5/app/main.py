from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .client import EventsApiClient
from .controller import CalendarController, create_calendar_router, register_error_handlers
from .service import CalendarService

app = FastAPI(
    title="EduEvent — Moduł 5: Kalendarz i harmonogram",
    description="Mikroserwis udostępniający publiczne API kalendarza (widok dzienny, tygodniowy, miesięczny).",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

events_client = EventsApiClient()
calendar_service = CalendarService(events_client)
calendar_controller = CalendarController(calendar_service)

register_error_handlers(app)
app.include_router(create_calendar_router(calendar_controller))

static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")