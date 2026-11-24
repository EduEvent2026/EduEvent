from fastapi import APIRouter, Depends, Query, status

from app.schemas.uzytkownik_response import UzytkownikResponse
from app.security.dependencies import require_role
from app.services.user_service import user_service

#endpoints require admin
router = APIRouter(
    prefix="/admin/users",
    tags=["Administrator"],
    dependencies=[Depends(require_role("admin"))],
)


@router.get("", response_model=list[UzytkownikResponse])
def pobierz_uzytkownikow(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    return user_service.pobierz_uzytkownikow(offset, limit)


@router.get("/{user_id}", response_model=UzytkownikResponse)
def pobierz_uzytkownika(user_id: str):
    return user_service.pobierz_uzytkownika(user_id)


@router.post("/{user_id}/block", status_code=status.HTTP_204_NO_CONTENT)
def zablokuj_uzytkownika(user_id: str):
    user_service.zablokuj_uzytkownika(user_id)


@router.put("/{user_id}/roles/{rola}", status_code=status.HTTP_204_NO_CONTENT)
def przypisz_role(user_id: str, rola: str):
    user_service.przypisz_role(user_id, rola)


@router.delete("/{user_id}/roles/{rola}", status_code=status.HTTP_204_NO_CONTENT)
def odbierz_role(user_id: str, rola: str):
    user_service.odbierz_role(user_id, rola)


@router.post("/{user_id}/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def wyslij_reset_hasla(user_id: str):
    user_service.wyslij_reset_hasla(user_id)
