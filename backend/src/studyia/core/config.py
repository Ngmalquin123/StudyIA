from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/.env, sin importar desde qué carpeta se lance la API
ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    app_name: str = "StudyIA"
    app_env: str = "development"
    database_url: str

    # JWT
    secret_key: str = Field(min_length=32)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    # El refresh token mantiene la sesión abierta sin pedir la contraseña otra vez
    refresh_token_expire_days: int = 7

    # Intentos fallidos de login permitidos por email+IP antes de bloquear
    login_max_attempts: int = 5
    login_lockout_minutes: int = 15

    # Orígenes permitidos para el frontend (Angular corre en el 4200)
    cors_origins: list[str] = ["http://localhost:4200"]

    llm_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("secret_key")
    @classmethod
    def secret_key_not_placeholder(cls, value: str) -> str:
        if value.startswith("CAMBIAR"):
            raise ValueError(
                "SECRET_KEY sigue con el valor de ejemplo. Genera una con: "
                "python -c \"import secrets; print(secrets.token_urlsafe(48))\""
            )
        return value

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


settings = Settings()
