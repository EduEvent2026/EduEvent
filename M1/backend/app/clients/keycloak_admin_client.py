import time

import httpx

from app.config import settings
from app.exceptions import Konflikt, KeycloakBlad, NieZnaleziono


class KeycloakAdminClient:
    #Klient Admin REST API Keycloaka

    def __init__(self):
        self._http = httpx.Client(timeout=10)
        self._token: str | None = None
        self._wygasa: float = 0.0

    #autoryzacja

    def _pobierz_token(self) -> str:
        if self._token and time.time() < self._wygasa - 10:
            return self._token
        try:
            r = self._http.post(
                f"{settings.oidc_base}/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": settings.keycloak_admin_client_id,
                    "client_secret": settings.keycloak_admin_client_secret,
                },
            )
        except httpx.HTTPError as e:
            raise KeycloakBlad("Keycloak jest niedostępny") from e
        if r.status_code != 200:
            raise KeycloakBlad(
                f"Nie udało się uzyskać tokena service account (HTTP {r.status_code})"
            )
        dane = r.json()
        self._token = dane["access_token"]
        self._wygasa = time.time() + dane.get("expires_in", 60)
        return self._token

    def _request(self, method: str, sciezka: str, **kwargs) -> httpx.Response:
        try:
            r = self._http.request(
                method,
                f"{settings.admin_api_base}{sciezka}",
                headers={"Authorization": f"Bearer {self._pobierz_token()}"},
                **kwargs,
            )
        except httpx.HTTPError as e:
            raise KeycloakBlad("Keycloak jest niedostępny") from e
        if r.status_code == 404:
            raise NieZnaleziono(sciezka)
        if r.status_code == 409:
            raise Konflikt("Dane kolidują z istniejącym użytkownikiem")
        if r.status_code >= 400:
            raise KeycloakBlad(f"Keycloak zwrócił HTTP {r.status_code}")
        return r

    #użytkownicy

    def pobierz_uzytkownika(self, user_id: str) -> dict:
        return self._request("GET", f"/users/{user_id}").json()

    def pobierz_uzytkownikow(self, offset: int = 0, limit: int = 50) -> list[dict]:
        return self._request(
            "GET", "/users", params={"first": offset, "max": limit}
        ).json()

    def aktualizuj_uzytkownika(self, user_id: str, dane: dict) -> None:
        aktualne = self.pobierz_uzytkownika(user_id)
        aktualne.update(dane)
        self._request("PUT", f"/users/{user_id}", json=aktualne)

    def zablokuj_uzytkownika(self, user_id: str) -> None:
        self.aktualizuj_uzytkownika(user_id, {"enabled": False})
        self._request("POST", f"/users/{user_id}/logout")

    #role

    def pobierz_role_uzytkownika(self, user_id: str) -> list[str]:
        r = self._request("GET", f"/users/{user_id}/role-mappings/realm")
        return [rola["name"] for rola in r.json()]

    def przypisz_role(self, user_id: str, rola: str) -> None:
        reprezentacja = self._request("GET", f"/roles/{rola}").json()
        self._request(
            "POST", f"/users/{user_id}/role-mappings/realm", json=[reprezentacja]
        )

    def odbierz_role(self, user_id: str, rola: str) -> None:
        reprezentacja = self._request("GET", f"/roles/{rola}").json()
        self._request(
            "DELETE", f"/users/{user_id}/role-mappings/realm", json=[reprezentacja]
        )

    #hasło

    def wyslij_reset_hasla(self, user_id: str) -> None:
        """Wymaga skonfigurowanego SMTP w realmie i adresu email użytkownika."""
        self._request(
            "PUT", f"/users/{user_id}/execute-actions-email", json=["UPDATE_PASSWORD"]
        )


keycloak_admin_client = KeycloakAdminClient()
