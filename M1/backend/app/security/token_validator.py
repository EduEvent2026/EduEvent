import jwt

from app.clients.keycloak_oidc_client import KeycloakOIDCClient
from app.exceptions import KeycloakBlad, TokenNieprawidlowy


class TokenValidator:
    def __init__(self, oidc_client: KeycloakOIDCClient, issuer: str, client_id: str):
        self._oidc = oidc_client
        self._issuer = issuer
        self._client_id = client_id

    def weryfikuj_token(self, token: str) -> dict:
        try:
            klucz = self._oidc.pobierz_klucz_publiczny(token)
            claims = jwt.decode(
                token,
                klucz,
                algorithms=["RS256"],
                issuer=self._issuer,
                options={"verify_aud": False},
            )
        except jwt.PyJWKClientConnectionError as e:
            raise KeycloakBlad("Nie można pobrać kluczy publicznych z Keycloaka") from e
        except jwt.ExpiredSignatureError as e:
            raise TokenNieprawidlowy("Token wygasł") from e
        except jwt.PyJWTError as e:
            raise TokenNieprawidlowy("Nieprawidłowy token") from e

        if claims.get("azp") != self._client_id:
            raise TokenNieprawidlowy("Token wystawiony dla innego klienta")
        return claims

    @staticmethod
    def sprawdz_role(claims: dict, rola: str) -> bool:
        return rola in claims.get("realm_access", {}).get("roles", [])
