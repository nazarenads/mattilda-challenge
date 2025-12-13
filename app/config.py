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

    # Authentication
    secret_key: str = Field(
        default="change-me-in-production",
        validation_alias="SECRET_KEY",
    )
    access_token_expire_minutes: int = Field(
        default=1440,  # 24 hours
        validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )

    # Admin user (created on startup if doesn't exist)
    admin_email: str = Field(
        default="admin@example.com",
        validation_alias="ADMIN_EMAIL",
    )
    admin_password: str = Field(
        default="changeme",
        validation_alias="ADMIN_PASSWORD",
    )

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


settings = Settings()
