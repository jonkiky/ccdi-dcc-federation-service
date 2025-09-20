"""
Core configuration settings for the CCDI Federation Service.

This module uses pydantic-settings for configuration management, supporting
environment variables and .env files.
"""

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = Field(default="CCDI Federation Service", alias="APP_NAME")
    app_version: str = Field(default="v1.2.0", alias="APP_VERSION")
    debug: bool = Field(default=False, alias="DEBUG")
    
    # Server
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    
    # Database (Memgraph)
    memgraph_uri: str = Field(
        default="bolt://localhost:7687", 
        alias="MEMGRAPH_URI"
    )
    memgraph_user: str = Field(default="", alias="MEMGRAPH_USER")
    memgraph_password: str = Field(default="", alias="MEMGRAPH_PASSWORD")
    memgraph_database: str = Field(default="memgraph", alias="MEMGRAPH_DATABASE")
    memgraph_max_connection_lifetime: int = Field(
        default=3600, 
        alias="MEMGRAPH_MAX_CONNECTION_LIFETIME"
    )
    memgraph_max_connection_pool_size: int = Field(
        default=50, 
        alias="MEMGRAPH_MAX_CONNECTION_POOL_SIZE"
    )
    
    # Redis (optional for caching)
    redis_url: Optional[str] = Field(
        default=None, 
        alias="REDIS_URL"
    )
    
    # Pagination defaults
    default_page_size: int = Field(default=100, alias="DEFAULT_PAGE_SIZE")
    max_page_size: int = Field(default=1000, alias="MAX_PAGE_SIZE")
    
    # Cache settings
    cache_enabled: bool = Field(default=True, alias="CACHE_ENABLED")
    cache_ttl_count_endpoints: int = Field(
        default=1800,  # 30 minutes
        alias="CACHE_TTL_COUNT_ENDPOINTS"
    )
    cache_ttl_summary_endpoints: int = Field(
        default=900,   # 15 minutes
        alias="CACHE_TTL_SUMMARY_ENDPOINTS"
    )
    cache_ttl_list_endpoints: int = Field(
        default=300,   # 5 minutes
        alias="CACHE_TTL_LIST_ENDPOINTS"
    )
    
    # Security
    cors_origins: list[str] = Field(
        default=["*"], 
        alias="CORS_ORIGINS"
    )
    cors_credentials: bool = Field(default=True, alias="CORS_CREDENTIALS")
    cors_methods: list[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        alias="CORS_METHODS"
    )
    cors_headers: list[str] = Field(
        default=["*"],
        alias="CORS_HEADERS"
    )
    
    # Rate limiting
    rate_limit_enabled: bool = Field(default=True, alias="RATE_LIMIT_ENABLED")
    rate_limit_requests_per_minute: int = Field(
        default=60, 
        alias="RATE_LIMIT_REQUESTS_PER_MINUTE"
    )
    
    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")  # json or text
    
    # Data sharing policies
    share_line_level_data: bool = Field(
        default=True, 
        alias="SHARE_LINE_LEVEL_DATA"
    )
    
    # Organization and server info
    organization_name: str = Field(
        default="Example Organization",
        alias="ORGANIZATION_NAME"
    )
    server_name: str = Field(
        default="Example CCDI Federation Node",
        alias="SERVER_NAME"
    )
    contact_email: str = Field(
        default="support@example.com",
        alias="CONTACT_EMAIL"
    )
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
