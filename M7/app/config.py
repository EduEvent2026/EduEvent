from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "mysql+pymysql://eduevent:eduevent@localhost:3306/eduevent_notifications"
    events_api_url: str = "http://localhost:8002"
    keycloak_jwks_url: str = "http://localhost:8080/realms/eduevent/protocol/openid-connect/certs"
    keycloak_issuer: str = "http://localhost:8080/realms/eduevent"
    reminder_interval_seconds: int = 60

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()