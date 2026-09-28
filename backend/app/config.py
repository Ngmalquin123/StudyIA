"""
StudyIA - Configuracion del backend.

Lee las variables de entorno del archivo .env y las expone como atributos
con nombre. Se importa una sola vez: `from app.config import settings`.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Ruta absoluta al .env. La calculamos desde la ubicacion de este archivo
# para que funcione sin importar desde donde se ejecute el backend.
BACKEND_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    """Valores de configuracion del proyecto, leidos del archivo .env."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Base de datos ---
    DATABASE_URL: str
    # Poner en true hace que la terminal muestre cada consulta SQL que la app
    # manda a PostgreSQL. Se usa para demostrar que la API really hace SELECTs.
    DB_ECHO: bool = False

    # --- Autenticacion (JWT) ---
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120

    # --- Frontend (CORS) ---
    CORS_ORIGINS: str = "http://localhost:4200"

    # --- Proveedor de Inteligencia Artificial ---
    # "gemini" u "opencode". Cambiarlo aqui cambia de proveedor sin
    # tocar el resto del codigo.
    IA_PROVEEDOR: str = "gemini"

    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    OPENCODE_API_KEY: str = ""
    OPENCODE_BASE_URL: str = "https://opencode.ai/zen/v1"
    IA_MODEL: str = "space-bunny-free"

    @property
    def cors_origins_list(self) -> list[str]:
        """Convierte "http://a,http://b" en ["http://a", "http://b"]."""
        return [origen.strip() for origen in self.CORS_ORIGINS.split(",") if origen.strip()]

    @property
    def ia_api_key(self) -> str:
        """Devuelve la API key del proveedor que esta configurado."""
        if self.IA_PROVEEDOR == "opencode":
            return self.OPENCODE_API_KEY
        return self.GEMINI_API_KEY

    @property
    def ia_model(self) -> str:
        """Devuelve el nombre del modelo del proveedor configurado."""
        if self.IA_PROVEEDOR == "opencode":
            return self.IA_MODEL
        return self.GEMINI_MODEL


# Instancia unica. Todo el proyecto importa esta misma variable.
settings = Settings()
