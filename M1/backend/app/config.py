from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(ROOT_DIR / ".env"),
        extra="ignore",
    )

    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "eduevent"

    # Klient publiczny
    keycloak_client_id: str = "eduevent-frontend"

    # Klient confidential
    keycloak_admin_client_id: str = "eduevent-backend"
    keycloak_admin_client_secret: str = "eduevent-backend-secret"

    cors_origins: list[str] = ["http://localhost:3000"]

    @property
    def issuer(self) -> str:
        return f"{self.keycloak_url}/realms/{self.keycloak_realm}"

    @property
    def oidc_base(self) -> str:
        return f"{self.issuer}/protocol/openid-connect"

    @property
    def admin_api_base(self) -> str:
        return f"{self.keycloak_url}/admin/realms/{self.keycloak_realm}"


settings = Settings()
