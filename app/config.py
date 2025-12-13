import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env" if os.path.exists(".env") else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    debug: bool = False
    environment: str = "dev"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


settings = Settings()
