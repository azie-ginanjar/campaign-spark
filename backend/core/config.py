from pydantic import SecretStr
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    redis_url: str = "redis://localhost:6379/0"
    environment: str = "development"
    lemonsqueezy_webhook_secret: SecretStr = SecretStr("default_secret")
    openai_api_key: SecretStr = SecretStr("default_openai_key")
    gemini_api_key: SecretStr = SecretStr("default_gemini_key")
    
    class Config:
        env_file = ".env"

settings = Settings()
