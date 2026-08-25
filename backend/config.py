"""
Application settings loaded from environment variables.
All LLM API keys are server-side only — never exposed to client.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # LLM Provider API Keys — server-side only
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    google_api_key: str = ""

    # Supabase
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""

    # Monitoring
    sentry_dsn: str = ""
    environment: str = "development"

    # App
    frontend_url: str = "http://localhost:3000"
    vercel_token: str = ""


settings = Settings()
