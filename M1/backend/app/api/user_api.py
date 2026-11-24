from fastapi import APIRouter, Depends

from app.schemas.edycja_profilu_request import EdycjaProfiluRequest
from app.schemas.uzytkownik_response import UzytkownikResponse
from app.security.dependencies import get_current_user
from app.services.user_service import user_service

router = APIRouter(prefix="/me", tags=["Użytkownik"])

#endpoints user
@router.get("", response_model=UzytkownikResponse)
def pobierz_profil(claims: dict = Depends(get_current_user)):
    return user_service.pobierz_uzytkownika(claims["sub"])


@router.put("", response_model=UzytkownikResponse)
def edytuj_profil(
    dane: EdycjaProfiluRequest, claims: dict = Depends(get_current_user)
):
    return user_service.aktualizuj_profil(claims["sub"], dane)
