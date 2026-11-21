from dataclasses import dataclass
from uuid import UUID

import httpx
import jwt
from fastapi import Header
from jwt import PyJWKClient

from app.config import settings
from app.exceptions import forbidden_error, unauthorized_error


ROLE_PARTICIPANT = "PARTICIPANT"
ROLE_ORGANIZER = "ORGANIZER"
ROLE_ADMIN = "ADMIN"
ROLE_SERVICE = "SERVICE"  # Np. wywołania z Modułu 6 (Obecność)


@dataclass(frozen=True)
class CurrentUser:
    user_id: str
    roles: set[str]

    def has_any_role(self, *allowed_roles: str) -> bool:
        return bool(self.roles.intersection({r.upper() for r in allowed_roles}))


_jwks_client: PyJWKClient | None = None


def _get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        _jwks_client = PyJWKClient(settings.keycloak_jwks_url)
    return _jwks_client


async def _verify_via_auth_api(token: str) -> CurrentUser:
    """Alternatywna weryfikacja tokenu przez Moduł 1 (IAuthAPI)."""
    async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
        response = await client.get(
            f"{settings.auth_api_url}/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
    if response.status_code == 401:
        raise unauthorized_error("Token jest nieważny lub przedawniony")
    if response.status_code != 200:
        raise unauthorized_error("Nie udało się zweryfikować tożsamości")

    data = response.json()
    user_id = str(UUID(str(data["id"])))
    raw_roles = data.get("roles") or ([data["role"]] if "role" in data else [])
    roles = {str(r).upper() for r in raw_roles} or {ROLE_PARTICIPANT}
    return CurrentUser(user_id=user_id, roles=roles)


async def get_current_user(
    authorization: str | None = Header(default=None),
    x_dev_user_id: str | None = Header(default=None, alias="X-Dev-User-Id"),
    x_dev_roles: str | None = Header(default=None, alias="X-Dev-Roles"),
) -> CurrentUser:
    # Tryb developerski: pozwala testować endpointy bez działającego Keycloaka / Modułu 1
    if settings.dev_auth_bypass and not authorization:
        if not x_dev_user_id:
            raise unauthorized_error(
                "Brak tokenu Bearer (w trybie DEV podaj nagłówek X-Dev-User-Id z UUID)"
            )
        try:
            valid_uuid = str(UUID(x_dev_user_id))
        except ValueError as exc:
            raise unauthorized_error("Nieprawidłowy UUID w nagłówku X-Dev-User-Id") from exc

        roles = (
            {r.strip().upper() for r in x_dev_roles.split(",") if r.strip()}
            if x_dev_roles
            else {ROLE_PARTICIPANT}
        )
        return CurrentUser(user_id=valid_uuid, roles=roles)

    if not authorization or not authorization.startswith("Bearer "):
        raise unauthorized_error("Wymagany nagłówek Authorization: Bearer <token>")

    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise unauthorized_error("Pusty token uwierzytelniający")

    # 1. Próba lokalnej walidacji JWT z klucza publicznego Keycloak (OIDC)
    try:
        signing_key = _get_jwks_client().get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        sub = payload.get("sub")
        if not sub:
            raise unauthorized_error("Token nie zawiera identyfikatora użytkownika (sub)")

        user_id = str(UUID(str(sub)))
        realm_roles = payload.get("realm_access", {}).get("roles", [])
        roles = {str(r).upper() for r in realm_roles} or {ROLE_PARTICIPANT}
        return CurrentUser(user_id=user_id, roles=roles)
    except jwt.ExpiredSignatureError as exc:
        raise unauthorized_error("Token wygasł") from exc
    except jwt.PyJWTError:
        # 2. Fallback do Modułu 1 (IAuthAPI), jeśli token nie jest standardowym JWT z JWKS
        return await _verify_via_auth_api(token)


def require_roles(user: CurrentUser, *allowed_roles: str) -> None:
    if not user.has_any_role(*allowed_roles):
        raise forbidden_error()