from uuid import UUID
from fastapi import APIRouter, Depends
from app.config import settings
from app.domain.models import EventFilterSort
from app.integrations.module2_client import Module2Client
from app.services.catalog_service import CatalogService

router = APIRouter(prefix="/catalog", tags=["Catalog"])


def get_catalog_service() -> CatalogService:
    client = Module2Client(
        base_url=settings.module2_base_url,
        timeout=settings.module2_timeout,
    )
    return CatalogService(m2_client=client)


@router.get("/events")
async def list_catalog_events(
    params: EventFilterSort = Depends(),
    service: CatalogService = Depends(get_catalog_service),
):
    pass


@router.get("/events/{event_id}")
async def get_catalog_event_details(
    event_id: UUID,
    service: CatalogService = Depends(get_catalog_service),
):
    pass
