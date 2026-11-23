from app.clients.keycloak_admin_client import KeycloakAdminClient, keycloak_admin_client
from app.exceptions import NieprawidlowaRola
from app.schemas.edycja_profilu_request import EdycjaProfiluRequest
from app.schemas.uzytkownik_response import UzytkownikResponse

DOZWOLONE_ROLE = {"admin", "user"}

_POLA_KEYCLOAK = {"email": "email", "imie": "firstName", "nazwisko": "lastName"}


def _sprawdz_role(rola: str) -> None:
    if rola not in DOZWOLONE_ROLE:
        raise NieprawidlowaRola(
            f"Dozwolone role: {', '.join(sorted(DOZWOLONE_ROLE))}"
        )

class UserService:
    def __init__(self, admin_client: KeycloakAdminClient):
        self._kc = admin_client

    @staticmethod
    def _na_response(dane: dict, role: list[str] | None = None) -> UzytkownikResponse:
        return UzytkownikResponse(
            id=dane["id"],
            login=dane["username"],
            email=dane.get("email"),
            imie=dane.get("firstName"),
            nazwisko=dane.get("lastName"),
            role=[r for r in (role or []) if not r.startswith("default-roles-")],
        )

    def pobierz_uzytkownika(self, user_id: str) -> UzytkownikResponse:
        dane = self._kc.pobierz_uzytkownika(user_id)
        role = self._kc.pobierz_role_uzytkownika(user_id)
        return self._na_response(dane, role)

    def pobierz_uzytkownikow(
        self, offset: int = 0, limit: int = 50
    ) -> list[UzytkownikResponse]:
        return [
            self._na_response(u) for u in self._kc.pobierz_uzytkownikow(offset, limit)
        ]

    def aktualizuj_profil(
        self, user_id: str, dane: EdycjaProfiluRequest
    ) -> UzytkownikResponse:
        zmiany = {
            _POLA_KEYCLOAK[pole]: wartosc
            for pole, wartosc in dane.model_dump(exclude_none=True).items()
        }
        if zmiany:
            self._kc.aktualizuj_uzytkownika(user_id, zmiany)
        return self.pobierz_uzytkownika(user_id)

    def zablokuj_uzytkownika(self, user_id: str) -> None:
        self._kc.zablokuj_uzytkownika(user_id)

    def przypisz_role(self, user_id: str, rola: str) -> None:
        _sprawdz_role(rola)
        self._kc.przypisz_role(user_id, rola)

    def odbierz_role(self, user_id: str, rola: str) -> None:
        _sprawdz_role(rola)
        self._kc.odbierz_role(user_id, rola)

    def wyslij_reset_hasla(self, user_id: str) -> None:
        self._kc.wyslij_reset_hasla(user_id)


user_service = UserService(keycloak_admin_client)
