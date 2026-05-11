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
    sentry_dsn: str = ""

    @property
    def database_url_with_ssl(self) -> str:
        url = self.database_url
        if url and "sslmode=" not in url:
            url += "?sslmode=require"
        return url


settings = Settings()

os.environ.setdefault("GROQ_API_KEY", settings.groq_api_key)
os.environ.setdefault("GOOGLE_API_KEY", settings.google_api_key)
os.environ.setdefault("OPENAI_API_KEY", settings.openai_api_key)
os.environ.setdefault("TAVILY_API_KEY", settings.tavily_api_key)
