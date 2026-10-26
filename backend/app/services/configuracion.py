from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_RAIZ_PROYECTO = Path(__file__).resolve().parents[3]

class Configuracion(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_RAIZ_PROYECTO / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    supabase_url: str = Field(..., min_length=1)
    supabase_key: str = Field(..., min_length=1)
    cors_origins: str = Field(..., min_length=1)

    @property
    def cors_list(self) -> list[str]:
        return [origen.strip() for origen in self.cors_origins.split(",") if origen.strip()]

configuraciones = Configuracion()
