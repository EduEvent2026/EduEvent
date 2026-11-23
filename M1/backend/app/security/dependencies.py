from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2AuthorizationCodeBearer

from app.clients.keycloak_oidc_client import keycloak_oidc_client
from app.config import settings
from app.exceptions import TokenNieprawidlowy
from app.security.token_validator import TokenValidator

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"{settings.oidc_base}/auth",
    tokenUrl=f"{settings.oidc_base}/token",
)

token_validator = TokenValidator(
    oidc_client=keycloak_oidc_client,
    issuer=settings.issuer,
    client_id=settings.keycloak_client_id,
)


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        return token_validator.weryfikuj_token(token)
    except TokenNieprawidlowy as e:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_role(rola: str):
    def checker(claims: dict = Depends(get_current_user)) -> dict:
        if not token_validator.sprawdz_role(claims, rola):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Brak wymaganej roli")
        return claims

    return checker
