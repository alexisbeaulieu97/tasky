"""Tests for MCP server core functionality."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from tasky_mcp_server.config import MCPServerSettings
from tasky_mcp_server.errors import MCPTimeoutError
from tasky_mcp_server.server import MCPServer, request_id_var
from tasky_tasks.service import TaskService

from .conftest import InMemoryTaskRepository


def test_server_initialization() -> None:
    """Test that MCPServer initializes correctly."""
    settings = MCPServerSettings()
    server = MCPServer(settings)

    assert server.settings == settings
    assert server.server is not None
    assert len(server._service_cache) == 0  # noqa: SLF001


def test_set_request_context() -> None:
    """Test setting request context generates a unique request ID."""
    settings = MCPServerSettings()
    server = MCPServer(settings)

    request_id_1 = server.set_request_context()
    request_id_2 = server.set_request_context()

    assert request_id_1 != request_id_2
    assert len(request_id_1) > 0


def test_clear_service_cache(tmp_path: Path) -> None:
    """Test clearing the service cache."""
    settings = MCPServerSettings(project_path=tmp_path)
    server = MCPServer(settings)

    # Initialize a project and get service (which caches it)
    (tmp_path / ".tasky").mkdir()
    (tmp_path / ".tasky" / "config.toml").write_text('[backend]\nname = "json"\n')

    server.get_service()
    assert len(server._service_cache) == 1  # noqa: SLF001

    server.clear_service_cache()
    assert len(server._service_cache) == 0  # noqa: SLF001


def test_add_shutdown_hook() -> None:
    """Test adding shutdown hooks."""
    settings = MCPServerSettings()
    server = MCPServer(settings)

    called = []

    def hook() -> None:
        called.append(True)

    server.add_shutdown_hook(hook)
    assert len(server._shutdown_handlers) == 1  # noqa: SLF001


@pytest.mark.asyncio
async def test_shutdown_runs_hooks() -> None:
    """Test that shutdown runs all registered hooks."""
    settings = MCPServerSettings()
    server = MCPServer(settings)

    called = []

    def hook1() -> None:
        called.append(1)

    def hook2() -> None:
        called.append(2)

    server.add_shutdown_hook(hook1)
    server.add_shutdown_hook(hook2)

    await server.shutdown()

    assert called == [1, 2]


@pytest.mark.asyncio
async def test_handle_with_timeout_success() -> None:
    """Test handle_with_timeout with successful operation."""
    settings = MCPServerSettings(timeout_seconds=5)
    server = MCPServer(settings)

    async def quick_operation() -> str:
        return "success"

    result = await server.handle_with_timeout(quick_operation())
    assert result == "success"


@pytest.mark.asyncio
async def test_handle_with_timeout_exceeds() -> None:
    """Test handle_with_timeout raises MCPTimeoutError when exceeded."""
    settings = MCPServerSettings(timeout_seconds=1)
    server = MCPServer(settings)

    async def slow_operation() -> str:
        await asyncio.sleep(10)
        return "success"

    with pytest.raises(MCPTimeoutError, match="Operation timed out"):
        await server.handle_with_timeout(slow_operation(), timeout_seconds=0.1)


@pytest.mark.asyncio
async def test_run_tool_wraps_sync_handler(monkeypatch: pytest.MonkeyPatch) -> None:
    """run_tool should set request context and honor timeout overrides."""
    settings = MCPServerSettings()
    server = MCPServer(settings)
    captured: dict[str, int | None] = {"timeout": None}

    async def fake_handle(
        coro,
        *,
        timeout_seconds: int | None = None,
    ) -> object:
        captured["timeout"] = timeout_seconds
        return await coro

    monkeypatch.setattr(server, "handle_with_timeout", fake_handle)

    result = await server.run_tool("project_info", lambda: "ok", timeout_seconds=5)

    assert result == "ok"
    assert captured["timeout"] == 5
    assert request_id_var.get() == "no-request-id"


@pytest.mark.asyncio
async def test_run_tool_supports_async_handler() -> None:
    """run_tool should accept coroutine functions directly."""
    settings = MCPServerSettings()
    server = MCPServer(settings)

    async def handler(value: str) -> str:
        return value.upper()

    result = await server.run_tool("async", handler, "done")

    assert result == "DONE"


@pytest.mark.asyncio
async def test_list_tools_reports_all_registered_tools() -> None:
    """Ensure list_tools advertises all five Tasky tools."""
    settings = MCPServerSettings()
    server = MCPServer(settings)

    tools = await server._list_tools(None)

    assert {tool.name for tool in tools} == {
        "project_info",
        "create_tasks",
        "edit_tasks",
        "search_tasks",
        "get_tasks",
    }


@pytest.mark.asyncio
async def test_call_tool_project_info(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """call_tool should invoke project_info handler and include structured content."""
    settings = MCPServerSettings(project_path=tmp_path)
    server = MCPServer(settings)
    task_service = TaskService(InMemoryTaskRepository())
    monkeypatch.setattr(server, "get_service", lambda project_path=None: task_service)

    result = await server._call_tool("project_info", {})

    assert result.structuredContent is not None
    assert result.structuredContent["project_name"] == tmp_path.name
    assert not result.isError
