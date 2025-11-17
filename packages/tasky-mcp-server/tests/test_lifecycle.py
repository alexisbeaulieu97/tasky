"""Server lifecycle tests for MCP server."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from tasky_mcp_server.config import MCPServerSettings
from tasky_mcp_server.server import MCPServer


class TestServerLifecycle:
    """Test server startup and shutdown lifecycle."""

    def test_server_initialization_with_settings(
        self,
        temp_project_dir: Path,
    ) -> None:
        """Test server initializes with settings."""
        settings = MCPServerSettings(project_path=temp_project_dir)
        server = MCPServer(settings=settings)

        assert server.settings == settings
        assert server._service_cache == {}  # noqa: SLF001
        assert server._shutdown_handlers == []  # noqa: SLF001

    def test_server_initialization_creates_tasky_dir(
        self,
        tmp_path: Path,
    ) -> None:
        """Test server initialization creates .tasky directory if needed."""
        # Create .tasky directory
        tasky_dir = tmp_path / ".tasky"
        tasky_dir.mkdir()

        settings = MCPServerSettings(project_path=tmp_path)
        server = MCPServer(settings=settings)

        assert server.settings.project_path == tmp_path

    @pytest.mark.asyncio
    async def test_server_shutdown_executes_hooks(
        self,
    ) -> None:
        """Test shutdown executes all registered hooks."""
        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            tasky_dir = tmp_path / ".tasky"
            tasky_dir.mkdir()

            settings = MCPServerSettings(project_path=tmp_path)
            server = MCPServer(settings=settings)

        # Track shutdown calls
        calls: list[str] = []

        def hook1() -> None:
            calls.append("hook1")

        def hook2() -> None:
            calls.append("hook2")

        server.add_shutdown_hook(hook1)
        server.add_shutdown_hook(hook2)

        await server.shutdown()

        assert calls == ["hook1", "hook2"]

    @pytest.mark.asyncio
    async def test_server_shutdown_handles_hook_errors(
        self,
    ) -> None:
        """Test shutdown continues even if hooks fail."""
        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            tasky_dir = tmp_path / ".tasky"
            tasky_dir.mkdir()

            settings = MCPServerSettings(project_path=tmp_path)
            server = MCPServer(settings=settings)

        calls: list[str] = []

        def failing_hook() -> None:
            calls.append("failing")
            raise RuntimeError("Hook failed")  # noqa: EM101, TRY003

        def success_hook() -> None:
            calls.append("success")

        server.add_shutdown_hook(failing_hook)
        server.add_shutdown_hook(success_hook)

        # Should not raise, but logs error
        await server.shutdown()

        # Both hooks should be attempted
        assert "failing" in calls
        assert "success" in calls

    def test_service_caching_per_project(
        self,
        temp_project_dir: Path,
    ) -> None:
        """Test services are cached per project path."""
        # Ensure .tasky directory exists
        tasky_dir = temp_project_dir / ".tasky"
        tasky_dir.mkdir(exist_ok=True)

        settings = MCPServerSettings(project_path=temp_project_dir)
        server = MCPServer(settings=settings)

        # Get service twice
        # Act
        service1 = server.get_service()
        service2 = server.get_service()

        # Should be same instance
        assert service1 is service2
        assert len(server._service_cache) == 1  # noqa: SLF001

    def test_cache_clearing(
        self,
        temp_project_dir: Path,
    ) -> None:
        """Test clearing service cache."""
        # Ensure .tasky directory exists
        tasky_dir = temp_project_dir / ".tasky"
        tasky_dir.mkdir(exist_ok=True)

        settings = MCPServerSettings(project_path=temp_project_dir)
        server = MCPServer(settings=settings)

        # Create cached service
        _service = server.get_service()
        assert len(server._service_cache) == 1  # noqa: SLF001

        # Clear cache
        server.clear_service_cache()
        assert len(server._service_cache) == 0  # noqa: SLF001

        # Next call creates new instance
        new_service = server.get_service()
        assert len(server._service_cache) == 1  # noqa: SLF001
        assert new_service is not _service


class TestServerConfiguration:
    """Test server configuration options."""

    def test_default_configuration(self) -> None:
        """Test default server configuration."""
        settings = MCPServerSettings()

        # Assert
        assert settings.host == "127.0.0.1"
        assert settings.port == 8080
        assert settings.timeout_seconds == 60
        assert settings.max_concurrent_requests == 10

    def test_custom_configuration(
        self,
        temp_project_dir: Path,
    ) -> None:
        """Test custom server configuration."""
        settings = MCPServerSettings(
            host="0.0.0.0",  # noqa: S104
            port=9000,
            timeout_seconds=60,
            max_concurrent_requests=20,
            project_path=temp_project_dir,
        )

        assert settings.host == "0.0.0.0"  # noqa: S104
        assert settings.port == 9000
        assert settings.timeout_seconds == 60
        assert settings.max_concurrent_requests == 20
        assert settings.project_path == temp_project_dir

    def test_oauth_configuration(self) -> None:
        """Test OAuth configuration fields."""
        settings = MCPServerSettings(
            oauth_issuer_url="https://auth.example.com",
            oauth_client_id="client123",
            oauth_audience="api://tasky",
            oauth_resource="https://tasky.example.com",
        )

        assert settings.oauth_issuer_url == "https://auth.example.com"
        assert settings.oauth_client_id == "client123"
        assert settings.oauth_audience == "api://tasky"
        assert settings.oauth_resource == "https://tasky.example.com"
