from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

    DATABASE_URL: str = "mysql+aiomysql://root:rootpassword@mysql:3306/energy_device_db"
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    SERVICE_NAME: str = "device-service"
    LOG_LEVEL: str = "INFO"


settings = Settings()
