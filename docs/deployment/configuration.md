# Configuration Guide

## Overview

This guide covers all configuration options for the Clockify-ADO Automated Report system. Proper configuration is essential for successful deployment and operation.

## Environment Variables

### Core Configuration

Create a `.env` file in the project root with the following variables:

```bash
# Clockify Configuration
CLOCKIFY_API_KEY=your_clockify_api_key_here
CLOCKIFY_WORKSPACE_ID=your_workspace_id_here

# Azure DevOps Configuration  
ADO_ORG=your_organization_name
ADO_PROJECT=your_project_name
ADO_PAT=your_personal_access_token_here

# Optional: Advanced Configuration
CACHE_BACKEND=local  # Options: local, redis, sqlite
CACHE_TTL=3600  # Cache time-to-live in seconds
LOG_LEVEL=INFO  # Options: DEBUG, INFO, WARNING, ERROR
OUTPUT_FORMAT=excel  # Default output format
REPORT_TEMPLATE_DIR=templates  # Template directory path
```

### Environment-Specific Files

```bash
.env                # Default configuration
.env.development    # Development overrides
.env.staging       # Staging environment
.env.production    # Production environment
```

## Configuration File (config.yaml)

### Full Configuration Example

```yaml
# config.yaml
app:
  name: "Clockify-ADO Report Generator"
  version: "1.0.0"
  environment: ${ENV:-development}

clockify:
  api_key: ${CLOCKIFY_API_KEY}
  workspace_id: ${CLOCKIFY_WORKSPACE_ID}
  base_url: "https://api.clockify.me/api/v1"
  timeout: 30
  retry:
    max_attempts: 3
    backoff_factor: 2
  rate_limit:
    calls_per_second: 10

azure_devops:
  organization: ${ADO_ORG}
  project: ${ADO_PROJECT}
  pat: ${ADO_PAT}
  api_version: "7.0"
  base_url: "https://dev.azure.com"
  timeout: 30
  batch_size: 200
  retry:
    max_attempts: 3
    backoff_factor: 2

matching:
  patterns:
    - name: "hash_format"
      regex: '#(\d{4,6})'
      priority: 1
    - name: "ado_format"
      regex: 'ADO[-_]?(\d{4,6})'
      priority: 2
    - name: "wi_format"
      regex: 'WI[:_]?(\d{4,6})'
      priority: 3
    - name: "bracket_format"
      regex: '\[(\d{4,6})\]'
      priority: 4
    - name: "paren_format"
      regex: '\((\d{4,6})\)'
      priority: 5
    - name: "plain_number"
      regex: '\b(\d{4,6})\b'
      priority: 10
      validate: true
  
  fuzzy_matching:
    enabled: true
    threshold: 0.8
    max_candidates: 10
  
  conflict_resolution:
    strategy: "priority"  # Options: priority, first, all
    type_priority:
      - "Bug"
      - "Task"
      - "User Story"
      - "Feature"
      - "Epic"

cache:
  backend: ${CACHE_BACKEND:-local}
  ttl: ${CACHE_TTL:-3600}
  
  local:
    directory: ".cache"
    max_size_mb: 500
  
  redis:
    host: ${REDIS_HOST:-localhost}
    port: ${REDIS_PORT:-6379}
    password: ${REDIS_PASSWORD:-}
    db: ${REDIS_DB:-0}
    key_prefix: "clockify_ado:"
  
  sqlite:
    database: "cache.db"
    table: "cache_entries"

reporting:
  output_formats:
    - excel
    - html
    - json
  
  excel:
    template: "templates/excel_template.xlsx"
    sheets:
      - name: "Summary"
        type: "summary"
      - name: "ByPerson"
        type: "aggregation"
        group_by: ["user_name", "work_item_id"]
      - name: "ByWorkItem"
        type: "aggregation"
        group_by: ["work_item_id", "work_item_type"]
      - name: "RawData"
        type: "raw"
    formatting:
      header_style:
        bold: true
        bg_color: "#366092"
        font_color: "#FFFFFF"
      data_style:
        border: true
        alternating_rows: true
  
  html:
    template: "templates/report_template.html"
    theme: "dark"  # Options: dark, light
    charts:
      enabled: true
      library: "chartjs"
    tables:
      pagination: true
      items_per_page: 25
      sortable: true
      searchable: true
  
  json:
    pretty_print: true
    include_metadata: true
    date_format: "iso"

logging:
  level: ${LOG_LEVEL:-INFO}
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  
  handlers:
    console:
      enabled: true
      level: ${LOG_LEVEL:-INFO}
    
    file:
      enabled: true
      level: DEBUG
      filename: "logs/app.log"
      max_bytes: 10485760  # 10MB
      backup_count: 5
      rotation: "midnight"
    
    syslog:
      enabled: false
      host: "localhost"
      port: 514
      facility: "local0"

monitoring:
  metrics:
    enabled: true
    export_interval: 60  # seconds
    
    prometheus:
      enabled: false
      port: 9090
      path: "/metrics"
    
    statsd:
      enabled: false
      host: "localhost"
      port: 8125
      prefix: "clockify_ado"
  
  health_check:
    enabled: true
    port: 8080
    path: "/health"
    checks:
      - "clockify_connection"
      - "ado_connection"
      - "cache_connection"

scheduler:
  enabled: false
  timezone: "UTC"
  
  jobs:
    daily_report:
      enabled: true
      schedule: "0 9 * * *"  # 9 AM daily
      config:
        lookback_days: 1
        output_format: "excel"
        email_recipients:
          - "team-lead@example.com"
          - "project-manager@example.com"
    
    weekly_report:
      enabled: true
      schedule: "0 9 * * MON"  # 9 AM Monday
      config:
        lookback_days: 7
        output_format: "html"
        email_recipients:
          - "management@example.com"

notifications:
  email:
    enabled: false
    smtp:
      host: ${SMTP_HOST:-smtp.gmail.com}
      port: ${SMTP_PORT:-587}
      username: ${SMTP_USERNAME}
      password: ${SMTP_PASSWORD}
      use_tls: true
    from_address: "reports@example.com"
    templates:
      report_ready: "templates/email/report_ready.html"
      error_alert: "templates/email/error_alert.html"
  
  slack:
    enabled: false
    webhook_url: ${SLACK_WEBHOOK_URL}
    channel: "#reports"
    username: "Report Bot"
    icon_emoji: ":chart_with_upwards_trend:"
  
  teams:
    enabled: false
    webhook_url: ${TEAMS_WEBHOOK_URL}

security:
  encryption:
    enabled: true
    algorithm: "AES-256"
    key_derivation: "PBKDF2"
  
  api_keys:
    rotation_days: 90
    encryption: true
  
  rate_limiting:
    enabled: true
    max_requests_per_minute: 60
    max_requests_per_hour: 1000

performance:
  concurrent_requests: 5
  batch_processing:
    enabled: true
    batch_size: 100
  
  memory:
    max_heap_size: "2G"
    gc_threshold: 0.8
  
  database:
    connection_pool_size: 10
    query_timeout: 30

features:
  experimental:
    ai_matching: false
    predictive_analytics: false
    auto_categorization: false
  
  ui:
    enabled: false
    port: 3000
    host: "0.0.0.0"
```

## Pydantic Settings Class

```python
# app/config.py
from pydantic import BaseSettings, Field, validator
from typing import Optional, List, Dict, Any
from pathlib import Path
import yaml

class ClockifySettings(BaseSettings):
    api_key: str = Field(..., env="CLOCKIFY_API_KEY")
    workspace_id: str = Field(..., env="CLOCKIFY_WORKSPACE_ID")
    base_url: str = "https://api.clockify.me/api/v1"
    timeout: int = 30
    max_retries: int = 3

class AzureDevOpsSettings(BaseSettings):
    organization: str = Field(..., env="ADO_ORG")
    project: str = Field(..., env="ADO_PROJECT")
    pat: str = Field(..., env="ADO_PAT")
    api_version: str = "7.0"
    base_url: str = "https://dev.azure.com"
    timeout: int = 30
    batch_size: int = 200

class CacheSettings(BaseSettings):
    backend: str = Field("local", env="CACHE_BACKEND")
    ttl: int = Field(3600, env="CACHE_TTL")
    directory: Path = Path(".cache")
    
    # Redis settings (optional)
    redis_host: Optional[str] = Field(None, env="REDIS_HOST")
    redis_port: Optional[int] = Field(6379, env="REDIS_PORT")
    redis_password: Optional[str] = Field(None, env="REDIS_PASSWORD")

class LoggingSettings(BaseSettings):
    level: str = Field("INFO", env="LOG_LEVEL")
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_enabled: bool = True
    file_path: Path = Path("logs/app.log")
    console_enabled: bool = True

class Settings(BaseSettings):
    """Main application settings."""
    
    app_name: str = "Clockify-ADO Report Generator"
    environment: str = Field("development", env="ENV")
    
    # Sub-configurations
    clockify: ClockifySettings = ClockifySettings()
    azure_devops: AzureDevOpsSettings = AzureDevOpsSettings()
    cache: CacheSettings = CacheSettings()
    logging: LoggingSettings = LoggingSettings()
    
    # Report settings
    default_output_format: str = Field("excel", env="OUTPUT_FORMAT")
    report_template_dir: Path = Field(Path("templates"), env="REPORT_TEMPLATE_DIR")
    
    # Feature flags
    enable_fuzzy_matching: bool = True
    enable_caching: bool = True
    enable_metrics: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @classmethod
    def from_yaml(cls, yaml_path: Path) -> "Settings":
        """Load settings from YAML file."""
        with open(yaml_path, "r") as f:
            config = yaml.safe_load(f)
        return cls(**config)
    
    @validator("report_template_dir")
    def validate_template_dir(cls, v: Path) -> Path:
        """Ensure template directory exists."""
        v.mkdir(parents=True, exist_ok=True)
        return v

# Singleton instance
settings = Settings()
```

## Configuration Validation

```python
# app/config_validator.py
import sys
from typing import List, Tuple
from pathlib import Path

class ConfigValidator:
    """Validate configuration before application start."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate(self) -> Tuple[bool, List[str], List[str]]:
        """
        Validate all configuration.
        Returns: (is_valid, errors, warnings)
        """
        self._validate_api_keys()
        self._validate_paths()
        self._validate_cache()
        self._validate_templates()
        
        return len(self.errors) == 0, self.errors, self.warnings
    
    def _validate_api_keys(self):
        """Validate API keys are present and formatted correctly."""
        # Clockify API key
        if not self.settings.clockify.api_key:
            self.errors.append("CLOCKIFY_API_KEY is required")
        elif len(self.settings.clockify.api_key) < 20:
            self.warnings.append("CLOCKIFY_API_KEY seems too short")
        
        # ADO PAT
        if not self.settings.azure_devops.pat:
            self.errors.append("ADO_PAT is required")
        
        # Workspace ID
        if not self.settings.clockify.workspace_id:
            self.errors.append("CLOCKIFY_WORKSPACE_ID is required")
    
    def _validate_paths(self):
        """Validate required paths exist."""
        if not self.settings.report_template_dir.exists():
            self.warnings.append(
                f"Template directory {self.settings.report_template_dir} will be created"
            )
            self.settings.report_template_dir.mkdir(parents=True, exist_ok=True)
    
    def _validate_cache(self):
        """Validate cache configuration."""
        if self.settings.cache.backend == "redis":
            if not self.settings.cache.redis_host:
                self.errors.append("REDIS_HOST required for Redis cache backend")
        elif self.settings.cache.backend == "local":
            cache_dir = Path(self.settings.cache.directory)
            if not cache_dir.exists():
                cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _validate_templates(self):
        """Validate report templates exist."""
        template_files = [
            "excel_template.xlsx",
            "report_template.html"
        ]
        
        for template in template_files:
            template_path = self.settings.report_template_dir / template
            if not template_path.exists():
                self.warnings.append(f"Template {template} not found, will use default")

def validate_config():
    """Main validation entry point."""
    validator = ConfigValidator(settings)
    is_valid, errors, warnings = validator.validate()
    
    # Print warnings
    for warning in warnings:
        print(f"⚠️  WARNING: {warning}")
    
    # Print errors and exit if invalid
    if not is_valid:
        print("\n❌ Configuration validation failed:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    
    print("✅ Configuration validated successfully")
    return True
```

## Security Configuration

### Encrypting Sensitive Data

```python
# app/security/encryption.py
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import base64
import os

class ConfigEncryption:
    """Encrypt sensitive configuration values."""
    
    def __init__(self, password: str = None):
        if not password:
            password = os.getenv("CONFIG_ENCRYPTION_KEY", "default-key")
        
        # Derive key from password
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'stable-salt',  # Use proper salt in production
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        self.cipher = Fernet(key)
    
    def encrypt(self, value: str) -> str:
        """Encrypt a configuration value."""
        return self.cipher.encrypt(value.encode()).decode()
    
    def decrypt(self, encrypted: str) -> str:
        """Decrypt a configuration value."""
        return self.cipher.decrypt(encrypted.encode()).decode()

# Usage example
encryption = ConfigEncryption()

# Encrypt sensitive values
encrypted_pat = encryption.encrypt("your-actual-pat")
print(f"ADO_PAT={encrypted_pat}")

# In application, decrypt when needed
actual_pat = encryption.decrypt(os.getenv("ADO_PAT"))
```

## Dynamic Configuration

### Runtime Configuration Updates

```python
# app/config_manager.py
from typing import Any, Dict
import json
from pathlib import Path

class ConfigManager:
    """Manage runtime configuration changes."""
    
    def __init__(self, base_settings: Settings):
        self.base_settings = base_settings
        self.overrides: Dict[str, Any] = {}
        self.load_overrides()
    
    def load_overrides(self):
        """Load configuration overrides from file."""
        override_file = Path("config_overrides.json")
        if override_file.exists():
            with open(override_file, "r") as f:
                self.overrides = json.load(f)
    
    def save_overrides(self):
        """Save configuration overrides to file."""
        with open("config_overrides.json", "w") as f:
            json.dump(self.overrides, f, indent=2)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with overrides."""
        # Check overrides first
        if key in self.overrides:
            return self.overrides[key]
        
        # Then check base settings
        keys = key.split(".")
        value = self.base_settings
        for k in keys:
            value = getattr(value, k, default)
        
        return value
    
    def set(self, key: str, value: Any):
        """Set configuration override."""
        self.overrides[key] = value
        self.save_overrides()
    
    def reset(self, key: str):
        """Remove configuration override."""
        if key in self.overrides:
            del self.overrides[key]
            self.save_overrides()
```

## Testing Configuration

### Test Environment Setup

```bash
# .env.test
CLOCKIFY_API_KEY=test_api_key
CLOCKIFY_WORKSPACE_ID=test_workspace
ADO_ORG=test_org
ADO_PROJECT=test_project
ADO_PAT=test_pat
CACHE_BACKEND=memory
LOG_LEVEL=DEBUG
```

### Configuration Tests

```python
# tests/test_config.py
import pytest
from app.config import Settings

def test_load_from_env(monkeypatch):
    """Test loading configuration from environment."""
    monkeypatch.setenv("CLOCKIFY_API_KEY", "test_key")
    monkeypatch.setenv("ADO_ORG", "test_org")
    
    settings = Settings()
    assert settings.clockify.api_key == "test_key"
    assert settings.azure_devops.organization == "test_org"

def test_validation():
    """Test configuration validation."""
    settings = Settings(
        clockify={"api_key": "", "workspace_id": ""},
        azure_devops={"organization": "", "project": "", "pat": ""}
    )
    
    validator = ConfigValidator(settings)
    is_valid, errors, _ = validator.validate()
    
    assert not is_valid
    assert "CLOCKIFY_API_KEY is required" in errors
```

## Best Practices

1. **Never commit sensitive data** - Use environment variables
2. **Use different configs per environment** - Development, staging, production
3. **Validate early** - Check configuration on startup
4. **Provide defaults** - Sensible defaults for optional settings
5. **Document all options** - Clear documentation for each setting
6. **Use type hints** - Leverage Pydantic for type safety
7. **Encrypt sensitive data** - Protect API keys and tokens
8. **Version your config** - Track configuration changes
9. **Monitor config changes** - Log configuration updates
10. **Test configurations** - Unit test configuration loading

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Missing environment variable | Check .env file exists and is loaded |
| Invalid API key | Regenerate key from service provider |
| Cache connection failed | Verify cache backend is running |
| Template not found | Check template directory path |
| Permission denied | Ensure write permissions for logs/cache |

### Debug Mode

Enable debug mode for detailed configuration information:

```bash
LOG_LEVEL=DEBUG python -m app.main --debug
```

This will output:
- Loaded configuration values
- Configuration source (env, file, default)
- Validation results
- Connection test results