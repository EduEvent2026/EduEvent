from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "EduEvent - Attendance Service (Module 6)"

    database_url: str = (
        "mysql+pymysql://eduevent:eduevent@localhost:3306/eduevent_attendance"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()