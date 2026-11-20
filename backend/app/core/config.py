import os
import json
from typing import List, Union
from pydantic_settings import BaseSettings
from pydantic import field_validator, model_validator


class Settings(BaseSettings):
    PROJECT_NAME: str = "SentinelAI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    SECRET_KEY: str = "sentinelai_dev_insecure_jwt_secret_key_minimum_32chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    DATABASE_URL: str = "sqlite:///./sentinelai.db"
    
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_ENABLED: bool = False
    
    ALLOWED_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost",
        "https://sentinel-ai.pages.dev",
    ]
    
    # ML & Risk Weights
    RISK_WEIGHT_ML: float = 0.35
    RISK_WEIGHT_RULE: float = 0.30
    RISK_WEIGHT_CORRELATION: float = 0.20
    RISK_WEIGHT_THREAT_INTEL: float = 0.15
    
    AGENT_SHARED_SECRET: str = "sentinel_dev_agent_telemetry_secure_key_2026"
    
    # Optional initial administrator bootstrap from environment
    INITIAL_ADMIN_USERNAME: str = ""
    INITIAL_ADMIN_PASSWORD: str = ""
    INITIAL_ADMIN_EMAIL: str = ""

    @field_validator("ALLOWED_ORIGINS", mode="before")
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            if v.startswith("["):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @model_validator(mode="after")
    def validate_production_configuration(self):
        KNOWN_INSECURE_SECRETS = {
            "sentinelai_super_secret_jwt_key_change_in_production_min32chars",
            "sentinelai_dev_insecure_jwt_secret_key_minimum_32chars",
            "CHANGE_ME_GENERATE_A_SECURE_RANDOM_SECRET",
            "CHANGE_ME",
            "secret",
            "password",
            "admin"
        }
        KNOWN_INSECURE_AGENT_SECRETS = {
            "sentinel_agent_telemetry_secure_key_2026",
            "sentinel_dev_agent_telemetry_secure_key_2026",
            "CHANGE_ME",
            "agent_secret"
        }

        if self.ENVIRONMENT.lower() == "production":
            if self.SECRET_KEY in KNOWN_INSECURE_SECRETS or len(self.SECRET_KEY) < 32:
                raise ValueError(
                    "CRITICAL PRODUCTION SECURITY ERROR: SECRET_KEY is weak, default, or under 32 characters. "
                    "Generate a cryptographically secure random key for production."
                )
            if self.AGENT_SHARED_SECRET in KNOWN_INSECURE_AGENT_SECRETS or len(self.AGENT_SHARED_SECRET) < 16:
                raise ValueError(
                    "CRITICAL PRODUCTION SECURITY ERROR: AGENT_SHARED_SECRET is unchanged from default. "
                    "Configure a unique shared secret in production."
                )
            if self.DEBUG is True:
                raise ValueError(
                    "CRITICAL PRODUCTION SECURITY ERROR: DEBUG must be set to False in production mode."
                )
        return self

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
