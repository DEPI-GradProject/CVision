import os
from unittest.mock import patch


def test_settings_defaults():
    from config import Settings

    with patch.dict(
        os.environ,
        {
            "AUTH_JWT_SECRET": "",
            "DATABASE_URL": "",
            "GROQ_API_KEY": "",
        },
        clear=False,
    ):
        s = Settings(_env_file=None)
        assert s.database_url == ""
        assert s.faiss_allow_dangerous is False
        assert s.auth_jwt_lifetime_seconds == 3600
        assert s.cors_origins == "*"


def test_settings_from_env():
    from config import Settings

    with patch.dict(
        os.environ,
        {
            "DATABASE_URL": "postgresql://user:pass@localhost/db",
            "GROQ_API_KEY": "gsk_test",
            "AUTH_JWT_SECRET": "mysecret",
            "FAISS_ALLOW_DANGEROUS": "true",
            "CORS_ORIGINS": "http://localhost:3000",
        },
        clear=False,
    ):
        s = Settings()
        assert s.database_url == "postgresql://user:pass@localhost/db"
        assert s.groq_api_key == "gsk_test"
        assert s.auth_jwt_secret == "mysecret"
        assert s.faiss_allow_dangerous is True
        assert s.cors_origins == "http://localhost:3000"


def test_database_url_with_ssl_sqlite():
    from config import Settings

    s = Settings(database_url="sqlite:///./test.db")
    assert s.database_url_with_ssl == "sqlite:///./test.db"


def test_database_url_with_ssl_postgres():
    from config import Settings

    s = Settings(database_url="postgresql://user:pass@localhost/db")
    url = s.database_url_with_ssl
    assert url.startswith("postgresql://user:pass@localhost/db")
    assert "sslmode=require" in url


def test_database_url_with_ssl_existing_sslmode():
    from config import Settings

    s = Settings(database_url="postgresql://user:pass@localhost/db?sslmode=disable")
    assert "sslmode=disable" in s.database_url_with_ssl
    assert s.database_url_with_ssl.count("sslmode") == 1


def test_database_url_async_sqlite():
    from config import Settings

    s = Settings(database_url="sqlite:///./test.db")
    assert "sqlite+aiosqlite" in s.database_url_async


def test_database_url_async_postgres():
    from config import Settings

    s = Settings(database_url="postgresql://user:pass@localhost/db")
    url = s.database_url_async
    assert url.startswith("postgresql+asyncpg://")
    assert "ssl=require" in url


def test_env_defaults_set_on_import():
    with patch.dict(
        os.environ,
        {
            "GROQ_API_KEY": "gsk_env",
            "GOOGLE_API_KEY": "google_env",
        },
        clear=False,
    ):
        from importlib import reload

        import config as config_mod

        reload(config_mod)
        assert os.environ["GROQ_API_KEY"] == "gsk_env"
        assert os.environ["GOOGLE_API_KEY"] == "google_env"
