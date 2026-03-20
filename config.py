import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv


load_dotenv()


@dataclass
class Settings:
    app_name: str = os.getenv("APP_NAME", "Math Step Tutor")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///math_tutor.db")
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret-key")
    debug: bool = os.getenv("DEBUG", "True").lower() == "true"
    default_user: str = os.getenv("DEFAULT_USERNAME", "student")
    max_recent_problems: int = int(os.getenv("MAX_RECENT_PROBLEMS", "25"))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
