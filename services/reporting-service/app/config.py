from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

    DATABASE_URL: str = "mysql+aiomysql://root:rootpassword@mysql:3306/energy_reporting_db"
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    SERVICE_NAME: str = "reporting-service"
    LOG_LEVEL: str = "INFO"

    INFLUX_URL: str = "http://influxdb:8086"
    INFLUX_TOKEN: str = "my-super-secret-token"
    INFLUX_ORG: str = "factoryops"
    INFLUX_BUCKET: str = "telemetry"

    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_PUBLIC_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "reports"
    MINIO_SECURE: bool = False

    DEFAULT_TARIFF_RATE: float = 8.5

    DEVICE_SERVICE_URL: str = "http://device-service:8000"


settings = Settings()
