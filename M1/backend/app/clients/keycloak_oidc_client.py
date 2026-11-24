from jwt import PyJWKClient

from app.config import settings


class KeycloakOIDCClient:
    #OpenID Connect token authentication

    def __init__(self, jwks_url: str):
        self._jwks = PyJWKClient(jwks_url)

    def pobierz_klucz_publiczny(self, token: str):
        return self._jwks.get_signing_key_from_jwt(token).key


keycloak_oidc_client = KeycloakOIDCClient(f"{settings.oidc_base}/certs")
