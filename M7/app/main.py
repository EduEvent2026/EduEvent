import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.event_client import EventClient
from app.notification_service import NotificationService
from app.notifications_controller import NotificationsController


async def _reminder_worker() -> None:
    event_client = EventClient()
    while True:
        db = SessionLocal()
        try:
            service = NotificationService(db=db, event_client=event_client)
            service.process_due_reminders()
        finally:
            db.close()
        await asyncio.sleep(settings.reminder_interval_seconds)


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    task = asyncio.create_task(_reminder_worker())
    try:
        yield
    finally:
        task.cancel()


app = FastAPI(title="EduEvent - Module 7: Notifications (In-App)", lifespan=lifespan)
controller = NotificationsController()
app.include_router(controller.router)