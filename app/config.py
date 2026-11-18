from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, loaded from environment variables or a .env file."""

    database_url: str = "sqlite:///./clientflow.db"
    secret_key: str = "change-me-in-production-use-a-long-random-string"
    access_token_expire_minutes: int = 60
    jwt_algorithm: str = "HS256"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
