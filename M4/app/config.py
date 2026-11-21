from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "EduEvent - Registrations Service (Module 4)"
    database_url: str = (
        "mysql+pymysql://eduevent:eduevent@localhost:3306/eduevent_registrations"
    )

    events_api_url: str = "http://events:8002"
    auth_api_url: str = "http://auth:8001"
    notifications_api_url: str = "http://notifications:8007"
    keycloak_jwks_url: str = (
        "http://keycloak:8080/realms/eduevent/protocol/openid-connect/certs"
    )

    http_timeout_seconds: float = 5.0

    # Flagi ułatwiające lokalny rozwój bez postawionych pozostałych modułów
    dev_mock_external_apis: bool = True
    dev_auth_bypass: bool = True
    dev_default_event_capacity: int = 2

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()