"""
Configuration management for Vector Conversion Helper.
Loads settings from environment variables and .env file.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379")
    
    # Vercel Blob Storage
    blob_read_write_token: str = Field(default="")
    
    # Mailgun
    mailgun_api_key: str = Field(default="")
    mailgun_domain: str = Field(default="")
    mailgun_from_email: str = Field(default="")
    mailgun_region: str = Field(default="us")  # "us" or "eu"
    
    @property
    def mailgun_api_url(self) -> str:
        """Get Mailgun API URL based on region."""
        if self.mailgun_region.lower() == "eu":
            return f"https://api.eu.mailgun.net/v3/{self.mailgun_domain}/messages"
        return f"https://api.mailgun.net/v3/{self.mailgun_domain}/messages"
    
    # API Configuration
    cors_origins: str = Field(default="*")
    max_file_size_mb: int = Field(default=10)
    job_timeout_seconds: int = Field(default=30)
    
    # Computed properties
    @property
    def max_file_size_bytes(self) -> int:
        """Convert MB to bytes for file validation."""
        return self.max_file_size_mb * 1024 * 1024
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Using lru_cache means we only read the .env file once,
    not on every request.
    """
    return Settings()