# services/order-service/src/config.py
import os
from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class PostgresConfig:
    host: str
    port: int
    user: str
    password: str
    database: str
    min_size: int = 5
    max_size: int = 10
    
    @property
    def connection_string(self) -> str:
        return f"postgres://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class PulsarConfig:
    host: str
    port: int = 6650
    admin_port: int = 8080
    
    @property
    def service_url(self) -> str:
        return f"pulsar://{self.host}:{self.port}"
    
    @property
    def admin_url(self) -> str:
        return f"http://{self.host}:{self.admin_port}"


@dataclass
class ApiConfig:
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False


@dataclass
class AppConfig:
    postgresql: PostgresConfig
    pulsar: PulsarConfig
    api: ApiConfig = field(default_factory=lambda: ApiConfig())
    service_name: str = "order-service"


def load_config() -> AppConfig:
    """Load application configuration from environment variables"""
    return AppConfig(
        postgresql=PostgresConfig(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres"),
            database=os.getenv("POSTGRES_DB", "orders"),
        ),
        pulsar=PulsarConfig(
            host=os.getenv("PULSAR_HOST", "localhost"),
            port=int(os.getenv("PULSAR_PORT", "6650")),
            admin_port=int(os.getenv("PULSAR_ADMIN_PORT", "8080")),
        ),
        service_name=os.getenv("SERVICE_NAME", "order-service"),
    )
    