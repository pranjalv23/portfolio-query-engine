from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = ""
    google_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash-lite-preview-09-2025"
    backend_url: str = "http://localhost:8000"
    stats_cache_ttl: float = 30.0
    response_cache_max: int = 256

    @field_validator("database_url", mode="before")
    @classmethod
    def normalise_dsn(cls, v: str) -> str:
        if isinstance(v, str) and v.startswith("postgres://"):
            return "postgresql://" + v[len("postgres://"):]
        return v

    @property
    def use_postgres(self) -> bool:
        return self.database_url.startswith(("postgresql", "postgres"))


settings = Settings()
