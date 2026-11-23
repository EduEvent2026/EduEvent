from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    module2_base_url: str = "http://localhost:8001"
    module2_timeout: int = 5

    class Config:
        env_file = ".env"


settings = Settings()
