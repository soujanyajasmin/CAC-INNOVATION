import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "CTRL ALT CRAC INNOVATIONS"
    TAGLINE: str = "Next-Gen AI Solutions, Autonomous Agents & Enterprise Automation"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "ctrl-alt-crac-innovations-super-secret-key-2026-secure-jwt")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./cac_innovations.db")
    
    # AI / Provider Settings
    DEFAULT_AI_PROVIDER: str = "cac_internal_engine"
    SIMULATED_AI_ENABLED: bool = True
    
    # Document storage
    STORAGE_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "storage", "documents")

    model_config = SettingsConfigDict(case_sensitive=True)

settings = Settings()
