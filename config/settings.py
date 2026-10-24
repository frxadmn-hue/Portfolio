"""
Global configuration for Natura Siberica Enterprise AI Solutions.
Adheres to 12-factor application design and Pydantic v2 BaseSettings.
"""

from functools import lru_cache
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # General Environment
    APP_NAME: str = "Natura Siberica Enterprise Agents"
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # MRP & ERP Integration (InvenTree)
    INVENTREE_URL: str = Field(default="http://localhost:8000", description="InvenTree ERP API Host")
    INVENTREE_API_TOKEN: Optional[str] = Field(default=None, description="InvenTree User Auth Token")
    INVENTREE_TIMEOUT_SECONDS: float = 15.0
    INVENTREE_MOCK_FALLBACK: bool = Field(default=True, description="Fallback to local simulated ERP if unreachable")

    # Vector Storage (Qdrant On-Premise)
    QDRANT_HOST: str = Field(default="http://localhost:6333", description="Local Qdrant Daemon URL")
    QDRANT_API_KEY: Optional[str] = Field(default=None, description="Optional Qdrant API Key")
    QDRANT_COLLECTION_NAME: str = "natura_siberica_knowledge"
    EMBEDDING_DIMENSION: int = 384  # e.g., BAAI/bge-small-en-v1.5 or all-MiniLM-L6-v2

    # Legal Auditor Compliance Thresholds
    MAX_ACCEPTABLE_PENALTY_PCT: float = Field(default=0.1, description="Max daily penalty percentage (0.1%/day)")
    MAX_TOTAL_PENALTY_CAP_PCT: float = Field(default=5.0, description="Max aggregate contract liability cap (5%)")
    MAX_PAYMENT_DEFERRAL_DAYS: int = Field(default=40, description="Max payment deferral allowed under 381-FZ")

    # Cryptographic Privacy Vault (152-FZ)
    VAULT_SECRET_KEY: str = Field(
        default="eE95ZDJmUGt1bWlRMnZ3RjZ4M0Nrb0t2NlRzVlp2eWk=",
        description="Fernet symmetric encryption master key (base64 encoded)"
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
