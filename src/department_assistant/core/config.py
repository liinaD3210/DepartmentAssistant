# src/department_assistant/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Загружаем переменные из .env файла
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Telegram
    bot_token: str

    # Postgres
    postgres_host: str
    postgres_port: int
    postgres_db: str
    postgres_user: str
    postgres_password: str

    # MinIO
    minio_host: str
    minio_port: int
    minio_user: str
    minio_password: str
    minio_secure: bool

    gemini_api_key: str

    @property
    def postgres_dsn(self) -> str:
        """Data Source Name для подключения к PostgreSQL."""
        return (f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@"
                f"{self.postgres_host}:{self.postgres_port}/{self.postgres_db}")

# Создаем единственный экземпляр настроек, который будем импортировать в других файлах
settings = Settings()