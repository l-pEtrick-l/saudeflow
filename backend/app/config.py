"""Configuração central da aplicação (variáveis de ambiente)."""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    APP_NAME: str = "SaúdeFlow"
    ENV: str = "development"
    DEBUG: bool = True
    DEMO_MODE: bool = True

    DATABASE_URL: str = "sqlite:///./saudeFlow.db"
    SECRET_KEY: str = "dev-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Integrações externas
    CNES_BASE_URL: str = "https://apidadosabertos.saude.gov.br"
    DATASUS_BASE_URL: str = "https://apidadosabertos.saude.gov.br"
    IBGE_BASE_URL: str = "https://servicodados.ibge.gov.br/api/v1"
    VIACEP_BASE_URL: str = "https://viacep.com.br/ws"
    OSRM_BASE_URL: str = "https://router.project-osrm.org"

    SYNC_ENABLED: bool = False
    SYNC_INTERVAL_MINUTES: int = 360
    SYNC_RATE_LIMIT_RPM: int = 60
    SYNC_DEFAULT_UF: str = "SP"
    SYNC_DEFAULT_MUNICIPIO_IBGE: int = 3550308
    SYNC_MAX_PAGES: int = 20

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
