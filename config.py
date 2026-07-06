import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    database_url: str = ""
    groq_api_key: str = ""
    google_api_key: str = ""
    openai_api_key: str = ""
    tavily_api_key: str = ""

    chrome_browser_path: str = ""
    linkedin_location: str = "Egypt"
    scroll_pause_seconds: int = 5
    max_scrolls: int = 25
    final_wait_seconds: int = 30

    faiss_allow_dangerous: bool = False
    faiss_index_path: str = "Data/faiss_db"
    sentry_dsn: str = ""

    groq_model_large: str = "llama-3.3-70b-versatile"
    groq_model_fast: str = "llama-3.1-8b-instant"

    auth_jwt_secret: str = ""
    auth_jwt_lifetime_seconds: int = 3600
    auth_reset_token_secret: str = ""
    auth_verification_token_secret: str = ""

    cors_origins: str = "*"

    @property
    def database_url_with_ssl(self) -> str:
        url = self.database_url
        if not url or url.startswith("sqlite"):
            return url
        url = url.replace("&channel_binding=require", "").replace("?channel_binding=require", "")
        if "sslmode=" not in url:
            url += "?sslmode=require"
        return url

    @property
    def database_url_async(self) -> str:
        url = self.database_url
        if not url:
            return url
        if url.startswith("sqlite"):
            return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
        if url.startswith("postgresql://"):
            url = "postgresql+asyncpg://" + url[len("postgresql://") :]
        url = url.replace("&channel_binding=require", "")
        url = url.replace("?channel_binding=require", "")
        url = url.replace("sslmode=require", "ssl=require")
        url = url.replace("sslmode=prefer", "ssl=prefer")
        url = url.replace("sslmode=disable", "ssl=disable")
        if url and "ssl=" not in url and "sslmode=" not in url:
            url += "?ssl=require"
        return url


settings = Settings()

os.environ.setdefault("GROQ_API_KEY", settings.groq_api_key)
os.environ.setdefault("GOOGLE_API_KEY", settings.google_api_key)
os.environ.setdefault("OPENAI_API_KEY", settings.openai_api_key)
os.environ.setdefault("TAVILY_API_KEY", settings.tavily_api_key)
