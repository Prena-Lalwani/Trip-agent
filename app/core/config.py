import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Gemini
    google_api_key: str

    # External APIs
    openweather_api_key: str

    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60

    # LangSmith
    langchain_tracing_v2: str = "true"
    langchain_api_key: str
    langchain_project: str = "travel-planner"

    # Database
    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/travel_planner"
    )

    # Email
    email_host: str = "smtp.gmail.com"
    email_port: int = 587
    email_user: str = ""
    email_password: str = ""

    # URLs
    app_base_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:5173"

    class Config:
        env_file = ".env"


settings = Settings()

# LangChain reads from os.environ; set before any langchain import
os.environ["LANGCHAIN_TRACING_V2"] = settings.langchain_tracing_v2
os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
