"""Settings models for hierarchical configuration."""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LoggingSettings(BaseModel):
    """Logging configuration settings.

    Attributes:
        verbosity: Logging verbosity level (0=WARNING, 1=INFO, 2=DEBUG)
        format: Log output format ("standard", "json", or "minimal")

    """

    verbosity: int = Field(default=0, ge=0, le=2)
    format: Literal["standard", "json", "minimal"] = "standard"


class TaskDefaultsSettings(BaseModel):
    """Default settings for task creation.

    Attributes:
        priority: Default task priority (1-5, where 5 is highest)
        status: Default task status when created

    """

    priority: int = Field(default=3, ge=1, le=5)
    status: str = "pending"


class StorageSettings(BaseModel):
    """Storage backend configuration.

    Attributes:
        backend: Storage backend name (e.g., "json", "sqlite", "postgres")
        path: Relative path from .tasky/ directory to storage file/database

    """

    backend: str = "json"
    path: str = "tasks.json"


class ProjectRegistrySettings(BaseModel):
    """Project registry configuration settings.

    Attributes:
        registry_path: Path to the global project registry file
        discovery_paths: Directories to search for projects during auto-discovery

    """

    registry_path: Path = Field(default=Path.home() / ".tasky" / "registry.json")
    discovery_paths: list[Path] = Field(
        default_factory=lambda: [
            Path.home() / "projects",
            Path.home() / "workspace",
            Path.home() / "code",
            Path.home() / "dev",
            Path.home() / "src",
        ],
    )


class MCPServerSettings(BaseSettings):
    """Configuration for MCP server instances."""

    model_config = SettingsConfigDict(
        env_prefix="TASKY_MCP_",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str = Field(
        default="127.0.0.1",
        description="Host address to bind the MCP server to",
    )
    port: int = Field(
        default=8080,
        description="Port to bind the MCP server to",
        ge=1,
        le=65535,
    )
    timeout_seconds: int = Field(
        default=60,
        description="Request timeout in seconds",
        ge=1,
    )
    max_concurrent_requests: int = Field(
        default=10,
        description="Maximum number of concurrent requests",
        ge=1,
    )
    project_path: Path = Field(
        default_factory=Path.cwd,
        description="Project path for task operations",
    )
    oauth_issuer_url: str | None = Field(
        default=None,
        description="OAuth 2.1 provider issuer URL",
    )
    oauth_client_id: str | None = Field(
        default=None,
        description="OAuth client ID",
    )
    oauth_audience: str | None = Field(
        default=None,
        description="Expected token audience",
    )
    oauth_resource: str | None = Field(
        default=None,
        description="Resource indicator URI (RFC 8707)",
    )

    def oauth_enabled(self) -> bool:
        """Return True when OAuth configuration is fully provided."""
        return bool(
            self.oauth_issuer_url and self.oauth_client_id and self.oauth_audience,
        )


class AppSettings(BaseSettings):
    """Application-wide settings with hierarchical configuration.

    This settings class integrates with pydantic-settings to load configuration from:
    1. Model defaults (lowest precedence)
    2. Global config file (~/.tasky/config.toml)
    3. Project config file (.tasky/config.toml)
    4. Environment variables (TASKY_*)
    5. CLI overrides (highest precedence)

    Attributes:
        logging: Logging configuration
        task_defaults: Default task creation settings
        storage: Storage backend configuration
        project_registry: Project registry configuration
        mcp: MCP server configuration

    """

    model_config = SettingsConfigDict(
        env_prefix="TASKY_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    task_defaults: TaskDefaultsSettings = Field(default_factory=TaskDefaultsSettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    project_registry: ProjectRegistrySettings = Field(
        default_factory=ProjectRegistrySettings,
    )
    mcp: MCPServerSettings = Field(default_factory=MCPServerSettings)
