from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import delete as sql_delete, select
from sqlalchemy.orm import Session

from app.event_client import EventClient
from app.models import Notification, NotificationType, Reminder, ReminderStatus


class NotificationService:
    def __init__(self, db: Session, event_client: EventClient) -> None:
        self._db = db
        self._event_client = event_client

    async def handle_m4_event(
        self,
        user_id: str,
        event_id: str,
        event_type: NotificationType,
    ) -> None:
        details = await self._event_client.get_event_details(event_id)

        if event_type == NotificationType.WAITLIST_PROMOTED:
            title = f"Awans z listy rezerwowej: {details.title}"
            message = f"Zwolniło się miejsce na wydarzenie '{details.title}'."
        else:
            title = f"Potwierdzenie zapisu: {details.title}"
            message = f"Zostałeś zapisany na wydarzenie '{details.title}'."

        notification = Notification(
            recipient_user_id=user_id,
            external_event_id=event_id,
            type=event_type,
            title=title,
            message=message,
            is_read=False,
        )
        self._db.add(notification)

        reminder = Reminder(
            recipient_user_id=user_id,
            external_event_id=event_id,
            event_title=details.title,
            scheduled_for=details.starts_at - timedelta(hours=24),
            status=ReminderStatus.SCHEDULED,
        )
        self._db.add(reminder)
        self._db.commit()

    def handle_m2_change(
        self,
        event_id: str,
        title: str | None,
        user_ids: list[str] | None,
        new_starts_at: datetime | None,
        event_type: NotificationType = NotificationType.EVENT_CHANGED,
    ) -> None:
        active_reminders = list(
            self._db.scalars(
                select(Reminder).where(
                    Reminder.external_event_id == event_id,
                    Reminder.status == ReminderStatus.SCHEDULED,
                )
            ).all()
        )

        target_users = list(dict.fromkeys(user_ids)) if user_ids else list(
            dict.fromkeys(r.recipient_user_id for r in active_reminders)
        )
        resolved_title = title or (active_reminders[0].event_title if active_reminders else f"Wydarzenie {event_id}")

        if event_type == NotificationType.EVENT_CANCELLED:
            notif_title = f"Odwołano wydarzenie: {resolved_title}"
            notif_message = f"Wydarzenie '{resolved_title}' zostało odwołane."
        else:
            notif_title = f"Zmiana w wydarzeniu: {resolved_title}"
            notif_message = f"Zaktualizowano szczegóły wydarzenia '{resolved_title}'."

        for uid in target_users:
            self._db.add(
                Notification(
                    recipient_user_id=uid,
                    external_event_id=event_id,
                    type=event_type,
                    title=notif_title,
                    message=notif_message,
                    is_read=False,
                )
            )

        for reminder in active_reminders:
            if event_type == NotificationType.EVENT_CANCELLED:
                reminder.status = ReminderStatus.CANCELLED
            elif new_starts_at is not None:
                reminder.scheduled_for = new_starts_at - timedelta(hours=24)
                if title:
                    reminder.event_title = title

        self._db.commit()

    def process_due_reminders(self) -> int:
        now = datetime.now(timezone.utc)
        due_reminders = list(
            self._db.scalars(
                select(Reminder).where(
                    Reminder.status == ReminderStatus.SCHEDULED,
                    Reminder.scheduled_for <= now,
                )
            ).all()
        )

        for reminder in due_reminders:
            self._db.add(
                Notification(
                    recipient_user_id=reminder.recipient_user_id,
                    external_event_id=reminder.external_event_id,
                    type=NotificationType.REMINDER,
                    title=f"Przypomnienie: {reminder.event_title}",
                    message=f"Wydarzenie '{reminder.event_title}' rozpocznie się za mniej niż 24 godziny.",
                    is_read=False,
                )
            )
            reminder.status = ReminderStatus.SENT

        if due_reminders:
            self._db.commit()

        return len(due_reminders)

    def get_user_history(self, user_id: str) -> list[Notification]:
        return list(
            self._db.scalars(
                select(Notification)
                .where(Notification.recipient_user_id == user_id)
                .order_by(Notification.created_at.desc())
            ).all()
        )

    def mark_read(self, notification_id: int, user_id: str) -> None:
        notification = self._db.get(Notification, notification_id)
        if not notification:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
        if notification.recipient_user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        notification.is_read = True
        self._db.commit()

    def delete(self, notification_id: int, user_id: str) -> None:
        notification = self._db.get(Notification, notification_id)
        if not notification:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
        if notification.recipient_user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        self._db.execute(sql_delete(Notification).where(Notification.id == notification_id))
        self._db.commit()