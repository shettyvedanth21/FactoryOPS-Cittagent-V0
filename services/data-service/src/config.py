from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

    DEVICE_SERVICE_URL: str = "http://device-service:8000"
    RULE_ENGINE_URL: str = "http://rule-engine-service:8002"
    INFLUX_URL: str = "http://influxdb:8086"
    INFLUX_TOKEN: str = "factoryops-admin-token"
    INFLUX_ORG: str = "factoryops"
    INFLUX_BUCKET: str = "telemetry"
    MQTT_BROKER: str = "emqx"
    MQTT_PORT: int = 1883
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    SERVICE_NAME: str = "data-service"
    LOG_LEVEL: str = "INFO"
    
    DEVICE_DB_HOST: str = "mysql"
    DEVICE_DB_PORT: int = 3306
    DEVICE_DB_NAME: str = "energy_device_db"
    DEVICE_DB_USER: str = "root"
    DEVICE_DB_PASSWORD: str = "rootpassword"


settings = Settings()
