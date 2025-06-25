from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


# -------------------------------------------------------------------
# Глобальные переменные
# -------------------------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parents[2]


# -------------------------------------------------------------------
# Настройки окружения
# -------------------------------------------------------------------

class Settings(BaseSettings):
    """Настройки проекта, читаемые из .env файла."""

    # --- База данных ---
    DB_NAME: str
    DB_USER: str
    DB_PASS: str
    DB_HOST: str
    DB_PORT: int

    # --- Общие ---
    MODE: str
    SECRET_KEY: str
    JWT_LIFETIME_SECONDS: int = 3600

    @property
    def DATABASE_URL_asyncpg(self) -> str:
        """Формирование URL для подключения к БД через asyncpg."""
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    model_config = SettingsConfigDict(env_file=".env")


# -------------------------------------------------------------------
# Глобальный экземпляр настроек
# -------------------------------------------------------------------

settings = Settings()
