"""Configurazione centralizzata, letta dalle variabili d'ambiente."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Trascrizione (Groq)
    groq_api_key: str = ""
    groq_whisper_model: str = "whisper-large-v3"

    # Riscrittura (Anthropic)
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"

    # Storage (Supabase)
    supabase_url: str = ""
    supabase_service_key: str = ""

    # Rete / vari
    cors_origins: str = "*"
    ytdlp_cookies_file: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        raw = (self.cors_origins or "*").strip()
        if raw == "*":
            return ["*"]
        return [o.strip() for o in raw.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
