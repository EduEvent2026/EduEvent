from uuid import UUID
from fastapi import APIRouter, HTTPException, Query
from app.domain.schemas import CategoryCreate, EventCreate

router = APIRouter()


def pending() -> None:
    raise HTTPException(status_code=501, detail={"error": {"code": "NOT_IMPLEMENTED", "message": "Endpoint jest szkieletem; logika biznesowa i autoryzacja nie są jeszcze zaimplementowane."}})


@router.post("/events", status_code=501, tags=["Wydarzenia"])
def create_event(payload: EventCreate):
    pending()


@router.get("/events", tags=["Wydarzenia"])
def list_events(page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100)):
    pending()


@router.get("/events/{event_id}", tags=["Wydarzenia"])
def get_event(event_id: UUID):
    pending()


@router.patch("/events/{event_id}", tags=["Wydarzenia"])
def update_event(event_id: UUID, payload: EventCreate):
    pending()


@router.post("/events/{event_id}/publish", tags=["Wydarzenia"])
def publish_event(event_id: UUID):
    pending()


@router.post("/events/{event_id}/archive", tags=["Wydarzenia"])
def archive_event(event_id: UUID):
    pending()


@router.delete("/events/{event_id}", tags=["Wydarzenia"])
def delete_event(event_id: UUID):
    pending()


@router.get("/categories", tags=["Kategorie"])
def list_categories():
    pending()


@router.post("/categories", tags=["Kategorie"])
def create_category(payload: CategoryCreate):
    pending()


@router.patch("/categories/{category_id}", tags=["Kategorie"])
def update_category(category_id: UUID, payload: CategoryCreate):
    pending()


@router.delete("/categories/{category_id}", tags=["Kategorie"])
def delete_category(category_id: UUID):
    pending()
