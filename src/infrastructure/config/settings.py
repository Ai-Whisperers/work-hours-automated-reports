"""Application settings using Pydantic."""

from functools import lru_cache
from pathlib import Path
from typing import Optional, List
from enum import Enum

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Environment(str, Enum):
    """Application environment."""
    
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class LogLevel(str, Enum):
    """Logging levels."""
    
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class CacheBackend(str, Enum):
    """Cache backend types."""
    
    LOCAL = "local"
    REDIS = "redis"
    MEMORY = "memory"


class Settings(BaseSettings):
    """Application settings with validation.
    
    Following the 12-factor app methodology, configuration is
    loaded from environment variables with sensible defaults.
    """
    
    # Application settings
    app_name: str = "Clockify-ADO Report Generator"
    app_version: str = "1.0.0"
    environment: Environment = Field(
        Environment.DEVELOPMENT,
        env="ENVIRONMENT"
    )
    debug: bool = Field(False, env="DEBUG")
    
    # Clockify settings
    clockify_api_key: str = Field(..., env="CLOCKIFY_API_KEY")
    clockify_workspace_id: str = Field(..., env="CLOCKIFY_WORKSPACE_ID")
    clockify_base_url: str = Field(
        "https://api.clockify.me/api/v1",
        env="CLOCKIFY_BASE_URL"
    )
    clockify_timeout: int = Field(30, env="CLOCKIFY_TIMEOUT")
    clockify_max_retries: int = Field(3, env="CLOCKIFY_MAX_RETRIES")
    clockify_default_project_id: Optional[str] = Field(None, env="CLOCKIFY_DEFAULT_PROJECT_ID")

    # Azure DevOps settings (optional - only required for report generation)
    ado_organization: Optional[str] = Field(None, env="ADO_ORG")
    ado_project: Optional[str] = Field(None, env="ADO_PROJECT")
    ado_pat: Optional[str] = Field(None, env="ADO_PAT")
    ado_base_url: str = Field(
        "https://dev.azure.com",
        env="ADO_BASE_URL"
    )
    ado_api_version: str = Field("7.0", env="ADO_API_VERSION")
    ado_timeout: int = Field(30, env="ADO_TIMEOUT")
    ado_max_retries: int = Field(3, env="ADO_MAX_RETRIES")
    ado_batch_size: int = Field(200, env="ADO_BATCH_SIZE")
    
    # Cache settings
    cache_backend: CacheBackend = Field(
        CacheBackend.LOCAL,
        env="CACHE_BACKEND"
    )
    cache_ttl: int = Field(3600, env="CACHE_TTL")
    cache_directory: Path = Field(
        Path(".cache"),
        env="CACHE_DIRECTORY"
    )
    
    # Redis settings (optional)
    redis_host: Optional[str] = Field(None, env="REDIS_HOST")
    redis_port: int = Field(6379, env="REDIS_PORT")
    redis_password: Optional[str] = Field(None, env="REDIS_PASSWORD")
    redis_db: int = Field(0, env="REDIS_DB")
    redis_key_prefix: str = Field(
        "clockify_ado:",
        env="REDIS_KEY_PREFIX"
    )
    
    # Logging settings
    log_level: LogLevel = Field(LogLevel.INFO, env="LOG_LEVEL")
    log_file: Optional[Path] = Field(
        Path("logs/app.log"),
        env="LOG_FILE"
    )
    log_format: str = Field(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    log_to_console: bool = Field(True, env="LOG_TO_CONSOLE")
    log_to_file: bool = Field(True, env="LOG_TO_FILE")
    
    # Report settings
    default_output_format: str = Field("excel", env="OUTPUT_FORMAT")
    report_template_directory: Path = Field(
        Path("templates"),
        env="REPORT_TEMPLATE_DIR"
    )
    report_output_directory: Path = Field(
        Path("reports"),
        env="REPORT_OUTPUT_DIR"
    )
    
    # Performance settings
    max_concurrent_requests: int = Field(5, env="MAX_CONCURRENT_REQUESTS")
    request_timeout: int = Field(60, env="REQUEST_TIMEOUT")
    
    # Feature flags
    enable_caching: bool = Field(True, env="ENABLE_CACHING")
    enable_fuzzy_matching: bool = Field(True, env="ENABLE_FUZZY_MATCHING")
    enable_notifications: bool = Field(False, env="ENABLE_NOTIFICATIONS")
    enable_metrics: bool = Field(True, env="ENABLE_METRICS")
    
    # Notification settings (optional)
    smtp_host: Optional[str] = Field(None, env="SMTP_HOST")
    smtp_port: int = Field(587, env="SMTP_PORT")
    smtp_username: Optional[str] = Field(None, env="SMTP_USERNAME")
    smtp_password: Optional[str] = Field(None, env="SMTP_PASSWORD")
    smtp_use_tls: bool = Field(True, env="SMTP_USE_TLS")
    notification_from: Optional[str] = Field(None, env="NOTIFICATION_FROM")
    notification_recipients: List[str] = Field(
        default_factory=list,
        env="NOTIFICATION_RECIPIENTS"
    )
    
    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @field_validator("cache_directory", "report_template_directory", "report_output_directory", "log_file", mode="after")
    @classmethod
    def create_directories(cls, v: Optional[Path]) -> Optional[Path]:
        """Ensure directories exist."""
        if v and not v.exists():
            v.parent.mkdir(parents=True, exist_ok=True)
            if v.suffix:  # It's a file
                v.parent.mkdir(parents=True, exist_ok=True)
            else:  # It's a directory
                v.mkdir(parents=True, exist_ok=True)
        return v
    
    @field_validator("notification_recipients", mode="before")
    @classmethod
    def parse_recipients(cls, v):
        """Parse comma-separated recipients."""
        if isinstance(v, str):
            return [email.strip() for email in v.split(",") if email.strip()]
        return v
    
    @field_validator("debug", mode="after")
    @classmethod
    def set_debug_from_env(cls, v, info):
        """Set debug based on environment."""
        if hasattr(info, 'data') and info.data.get("environment") == Environment.DEVELOPMENT:
            return True
        return v

    def validate_ado_required(self):
        """Validate that ADO credentials are set when needed for reports.

        Call this method before using ADO-related functionality.

        Raises:
            ValueError: If ADO credentials are missing
        """
        if not self.ado_organization or not self.ado_project or not self.ado_pat:
            raise ValueError(
                "Azure DevOps credentials are required for report generation. "
                "Please set: ADO_ORG, ADO_PROJECT, and ADO_PAT environment variables."
            )
    
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == Environment.PRODUCTION
    
    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == Environment.DEVELOPMENT
    
    @property
    def is_testing(self) -> bool:
        """Check if running in testing."""
        return self.environment == Environment.TESTING
    
    @property
    def ado_url(self) -> str:
        """Get full Azure DevOps URL."""
        return f"{self.ado_base_url}/{self.ado_organization}"
    
    @property
    def redis_url(self) -> str:
        """Get Redis connection URL."""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    def get_log_level(self) -> str:
        """Get the appropriate log level."""
        if self.debug:
            return "DEBUG"
        return self.log_level.value

    def get(self, key: str, default=None):
        """Get setting value by key with optional default.

        This provides dict-like access to settings for backward compatibility.

        Args:
            key: Setting name (case-insensitive, converts to snake_case)
            default: Default value if setting not found

        Returns:
            Setting value or default
        """
        # Convert to lowercase and replace dashes with underscores
        attr_name = key.lower().replace("-", "_")
        return getattr(self, attr_name, default)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance.
    
    This ensures we only load and validate settings once,
    improving performance and consistency.
    """
    return Settings()


# Create a global settings instance
settings = get_settings()