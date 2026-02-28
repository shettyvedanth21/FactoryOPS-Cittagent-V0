from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    SERVICE_NAME: str = "analytics-service"
    HOST: str = "0.0.0.0"
    PORT: int = 8003
    
    # Database
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "password"
    MYSQL_DATABASE: str = "energy_analytics_db"
    
    # InfluxDB
    INFLUX_URL: str = "http://localhost:8086"
    INFLUX_TOKEN: str = "my-token"
    INFLUX_ORG: str = "factoryops"
    INFLUX_BUCKET: str = "telemetry"
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    
    # Job settings
    MAX_CONCURRENT_JOBS: int = 3
    JOB_TIMEOUT_MINUTES: int = 30
    
    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+aiomysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
    
    @property
    def SYNC_DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
    
    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
