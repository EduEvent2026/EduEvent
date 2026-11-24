import jwt
from jwt import PyJWKClient, PyJWTError

from app.config import settings


class TokenValidator:
    def __init__(self) -> None:
        self._jwk_client = PyJWKClient(settings.keycloak_jwks_url)

    def _decode(self, token: str) -> dict:
        signing_key = self._jwk_client.get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=settings.keycloak_issuer,
            options={"verify_aud": False},
        )

    def is_valid(self, token: str) -> bool:
        try:
            self._decode(token)
            return True
        except (PyJWTError, Exception):
            return False

    def extract_user_id(self, token: str) -> str:
        payload = self._decode(token)
        user_id = payload.get("sub") or payload.get("preferred_username")
        if not user_id:
            raise ValueError("Missing user identifier in JWT")
        return str(user_id)