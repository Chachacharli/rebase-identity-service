# Application settings from environment variables or .env file
import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    PROJECT_NAME: str = "rebase-base-identity-service"
    PROJECT_VERSION: str = "0.1.0"
    BASE_URL: str = "http://localhost:8000"

    # Login settings
    MAX_LOGIN_ATTEMPTS: int = 5

    # Authorization code store backend (memory | redis)
    AUTH_CODE_STORE: str = "memory"
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_ALG: str = "RS256"
    PRIVATE_KEY_PATH: str = "keys/private.pem"
    PUBLIC_KEY_PATH: str = "keys/public.pem"

    # Database
    DATABASE_URL: str = f"postgresql+psycopg2://{os.getenv('DATA_BASE_USER')}:{os.getenv('DATA_BASE_PASSWORD')}@{os.getenv('DATA_BASE_HOST')}:{os.getenv('DATA_BASE_PORT')}/{os.getenv('DATA_BASE_NAME')}"


# Mail settings
class MailSettings(BaseSettings):
    SMTP_SERVER: str = os.getenv("SMTP_SERVER")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD")


settings = Settings()
mail_settings = MailSettings()
