"""Application configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    api_key: str = "your-secret-api-key"
    openai_api_key: str = ""

    # Agent configuration
    model: str = "gpt-5.1"
    max_conversation_turns: int = 50

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
