from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = Field(
        default="postgresql://user:password@localhost:5432/db",
        validation_alias="DATABASE_URL",
    )

    # Application
    debug: bool = False
    environment: str = "dev"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


settings = Settings()
