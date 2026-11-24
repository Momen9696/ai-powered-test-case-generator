"""Runtime configuration.

Secrets are read from the environment. They are never returned by the API.
"""

from __future__ import annotations

import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=None if os.getenv("APP_DISABLE_DOTENV") == "1" else ".env",
        extra="ignore",
    )

    database_url: str = "sqlite:///./data/app.db"
    cors_origins: str = "http://localhost:5173,http://localhost:8080,http://127.0.0.1:5173"
    ai_provider: str = "mock"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = "https://api.openai.com/v1"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-5-haiku-latest"
    anthropic_base_url: str = "https://api.anthropic.com"
    generation_temperature: float = 0.2
    generation_max_tokens: int = 4000
    max_input_chars: int = 100_000
    max_upload_bytes: int = 100_000

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


def get_settings() -> Settings:
    return Settings()
