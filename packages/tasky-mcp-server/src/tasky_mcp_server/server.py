"""MCP server implementation with service caching and request tracing."""

from __future__ import annotations

import asyncio
import contextvars
import json
import logging
import threading
import uuid
from collections.abc import Awaitable, Callable, Coroutine, MutableMapping
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeVar

import mcp.types as mcp_types
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from pydantic import BaseModel, ValidationError
from tasky_settings import create_task_service
from tasky_tasks.service import TaskService

from tasky_mcp_server.errors import (
    MCPError,
    MCPTimeoutError,
    MCPValidationError,
    map_domain_error_to_mcp,
)
from tasky_mcp_server.tools import (
    CreateTasksRequest,
    CreateTasksResponse,
    EditTasksRequest,
    EditTasksResponse,
    GetTasksRequest,
    GetTasksResponse,
    ProjectInfoRequest,
    ProjectInfoResponse,
    SearchTasksRequest,
    SearchTasksResponse,
    create_tasks,
    edit_tasks,
    get_tasks,
    project_info,
    search_tasks,
)

if TYPE_CHECKING:
    from tasky_mcp_server.config import MCPServerSettings


@dataclass(frozen=True)
class ToolSpec:
    """Metadata describing a registered MCP tool."""

    name: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    handler: Callable[[TaskService, dict[str, Any]], dict[str, Any]]


# Generic type for request parsing helpers
RequestModel = TypeVar("RequestModel", bound=BaseModel)
HandlerResult = TypeVar("HandlerResult")


# Context variable for request correlation ID
request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id",
    default="no-request-id",
)

logger = logging.getLogger(__name__)


class RequestLoggingAdapter(logging.LoggerAdapter[logging.Logger]):
    """Logging adapter that includes request ID in log records."""

    def process(
        self,
        msg: str,
        kwargs: MutableMapping[str, Any],
    ) -> tuple[str, MutableMapping[str, Any]]:
        """Add request ID to log message.

        Args:
            msg: Log message
            kwargs: Additional keyword arguments

        Returns:
            Tuple of (message, kwargs) with request ID prepended

        """
        request_id = request_id_var.get()
        return f"[{request_id}] {msg}", kwargs


class MCPServer:
    """MCP server with service caching and request tracing.

    This server implements:
    - Service caching (project-keyed service instances)
    - Request ID correlation for tracing
    - Thread-safe logging adapter
    - Graceful shutdown hooks

    """

    def __init__(self, settings: MCPServerSettings) -> None:
        """Initialize the MCP server.

        Args:
            settings: Server configuration settings

        """
        self.settings = settings
        self._server = Server("tasky-mcp")
        self._service_cache: dict[Path, TaskService] = {}
        self._cache_lock = threading.RLock()
        self._shutdown_handlers: list[Callable[[], None]] = []
        self._concurrency_sem = asyncio.Semaphore(self.settings.max_concurrent_requests)

        # Set up request logging
        self.logger = RequestLoggingAdapter(
            logging.getLogger("tasky_mcp_server"),
            {},
        )
        self._tool_specs = self._build_tool_specs()
        self._server.list_tools()(self._list_tools)
        self._server.call_tool()(self._call_tool)

    def get_service(self, project_path: Path | None = None) -> TaskService:
        """Get or create a task service for the project.

        Services are cached per project path to avoid re-initialization.

        Args:
            project_path: Path to the project. Uses configured path if None.

        Returns:
            TaskService instance for the project

        """
        path = project_path or self.settings.project_path
        path = path.resolve()

        with self._cache_lock:
            if path not in self._service_cache:
                self.logger.info("Creating service for project: %s", path)
                self._service_cache[path] = create_task_service(path)

            return self._service_cache[path]

    def clear_service_cache(self) -> None:
        """Clear the service cache (useful for testing)."""
        with self._cache_lock:
            self._service_cache.clear()

    def add_shutdown_hook(self, handler: Callable[[], None]) -> None:
        """Add a shutdown handler to be called on server shutdown.

        Args:
            handler: Callable to execute during shutdown

        """
        self._shutdown_handlers.append(handler)

    async def shutdown(self) -> None:
        """Gracefully shutdown the server and run cleanup hooks."""
        self.logger.info("Shutting down MCP server")

        # Run shutdown hooks
        for handler in self._shutdown_handlers:
            try:
                handler()
            except BaseException:
                self.logger.exception("Error in shutdown hook")

        # Clear service cache
        self.clear_service_cache()

    def set_request_context(self) -> str:
        """Set a new request ID in the context.

        Returns:
            The generated request ID

        """
        request_id = str(uuid.uuid4())
        request_id_var.set(request_id)
        return request_id

    async def handle_with_timeout(
        self,
        coro: Coroutine[Any, Any, HandlerResult],
        *,
        timeout_seconds: float | None = None,
    ) -> HandlerResult:
        """Execute a coroutine with timeout enforcement.

        Args:
            coro: Coroutine to execute
            timeout_seconds: Timeout in seconds. Uses configured timeout if None.

        Returns:
            Result of the coroutine

        Raises:
            MCPTimeoutError: If the operation exceeds the timeout

        """
        timeout = timeout_seconds or self.settings.timeout_seconds

        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except TimeoutError as e:
            msg = f"Operation timed out after {timeout} seconds"
            raise MCPTimeoutError(msg) from e

    async def run_tool(
        self,
        tool_name: str,
        handler: Callable[..., Awaitable[HandlerResult]] | Callable[..., HandlerResult],
        /,
        *args: object,
        timeout_seconds: float | None = None,
        **kwargs: object,
    ) -> HandlerResult:
        """Execute a tool handler with request context, logging, and timeout enforcement.

        Args:
            tool_name: Name of the tool being executed (for logs/metrics)
            handler: Callable (sync or async) implementing the tool
            *args: Positional arguments for the handler
            timeout_seconds: Optional timeout override
            **kwargs: Keyword arguments for the handler

        Returns:
            Whatever the handler returns

        """
        request_id = self.set_request_context()
        self.logger.info(
            "Handling tool '%s' (request_id=%s)",
            tool_name,
            request_id,
        )
        try:
            async with self._concurrency_sem:
                if asyncio.iscoroutinefunction(handler):
                    coro = handler(*args, **kwargs)
                else:
                    coro = asyncio.to_thread(handler, *args, **kwargs)
                result = await self.handle_with_timeout(coro, timeout_seconds=timeout_seconds)
                self.logger.info("Completed tool '%s' (request_id=%s)", tool_name, request_id)
                return result
        finally:
            request_id_var.set("no-request-id")

    @property
    def server(self) -> Server:
        """Get the underlying MCP Server instance."""
        return self._server

    async def serve_stdio(self) -> None:
        """Run the MCP server over stdio transport."""
        init_options = self._server.create_initialization_options(NotificationOptions())
        async with stdio_server() as (read_stream, write_stream):
            await self._server.run(read_stream, write_stream, init_options)
        await self.shutdown()

    # ========== MCP Tool Registration ==========

    def _build_tool_specs(self) -> dict[str, ToolSpec]:
        return {
            "project_info": ToolSpec(
                name="project_info",
                description="Return project metadata, status options, and task counts.",
                input_schema=ProjectInfoRequest.model_json_schema(),
                output_schema=ProjectInfoResponse.model_json_schema(),
                handler=self._tool_project_info,
            ),
            "create_tasks": ToolSpec(
                name="create_tasks",
                description="Create one or more tasks.",
                input_schema=CreateTasksRequest.model_json_schema(),
                output_schema=CreateTasksResponse.model_json_schema(),
                handler=self._tool_create_tasks,
            ),
            "edit_tasks": ToolSpec(
                name="edit_tasks",
                description="Update, delete, or transition tasks in bulk.",
                input_schema=EditTasksRequest.model_json_schema(),
                output_schema=EditTasksResponse.model_json_schema(),
                handler=self._tool_edit_tasks,
            ),
            "search_tasks": ToolSpec(
                name="search_tasks",
                description="Find tasks using optional filters.",
                input_schema=SearchTasksRequest.model_json_schema(),
                output_schema=SearchTasksResponse.model_json_schema(),
                handler=self._tool_search_tasks,
            ),
            "get_tasks": ToolSpec(
                name="get_tasks",
                description="Retrieve full task details for specific IDs.",
                input_schema=GetTasksRequest.model_json_schema(),
                output_schema=GetTasksResponse.model_json_schema(),
                handler=self._tool_get_tasks,
            ),
        }

    async def _list_tools(
        self,
        _: mcp_types.ListToolsRequest | None = None,
    ) -> list[mcp_types.Tool]:
        return [
            mcp_types.Tool(
                name=spec.name,
                description=spec.description,
                inputSchema=spec.input_schema,
                outputSchema=spec.output_schema,
            )
            for spec in self._tool_specs.values()
        ]

    async def _call_tool(
        self,
        name: str,
        arguments: dict[str, Any] | None,
    ) -> mcp_types.CallToolResult:
        payload_args: dict[str, Any] = arguments or {}
        return await self.run_tool(name, self._execute_tool, name, payload_args)

    def _execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> mcp_types.CallToolResult:
        spec = self._tool_specs.get(tool_name)
        if spec is None:
            return self._error_call_result(MCPValidationError(f"Unknown tool '{tool_name}'"))

        service = self.get_service()
        try:
            payload = spec.handler(service, arguments)
        except MCPError as exc:
            return self._error_call_result(exc)
        except ValidationError as exc:
            return self._error_call_result(MCPValidationError(str(exc)))
        except Exception as exc:  # pragma: no cover - defensive  # noqa: BLE001
            return self._error_call_result(exc)
        return self._make_call_result(payload)

    def _make_call_result(self, payload: dict[str, Any]) -> mcp_types.CallToolResult:
        return mcp_types.CallToolResult(
            content=[mcp_types.TextContent(type="text", text=json.dumps(payload, indent=2))],
            structuredContent=payload,
        )

    def _error_call_result(self, error: Exception) -> mcp_types.CallToolResult:
        request_id = request_id_var.get()
        error_payload = self._build_error_payload(error, request_id)
        text_message = f"[{request_id}] {error_payload['error']['message']}"
        return mcp_types.CallToolResult(
            content=[mcp_types.TextContent(type="text", text=text_message)],
            structuredContent=error_payload,
            isError=True,
        )

    def _build_error_payload(self, error: Exception, request_id: str) -> dict[str, Any]:
        if isinstance(error, MCPError):
            mapped = map_domain_error_to_mcp(error)
            suggestions = error.suggestions
        else:
            mapped = map_domain_error_to_mcp(error)
            suggestions = None

        payload: dict[str, Any] = {
            "error": {
                "code": mapped["code"],
                "message": mapped["message"],
                "request_id": request_id,
            },
        }
        if suggestions:
            payload["error"]["suggestions"] = suggestions
        return payload

    # ========== Tool Logic ==========

    def _tool_project_info(self, service: TaskService, params: dict[str, Any]) -> dict[str, Any]:
        self._parse_request(ProjectInfoRequest, params)
        response = project_info(service, self.settings.project_path)
        return response.model_dump(mode="json")

    def _tool_create_tasks(self, service: TaskService, params: dict[str, Any]) -> dict[str, Any]:
        request = self._parse_request(CreateTasksRequest, params)
        response = create_tasks(service, request)
        return response.model_dump(mode="json")

    def _tool_edit_tasks(self, service: TaskService, params: dict[str, Any]) -> dict[str, Any]:
        request = self._parse_request(EditTasksRequest, params)
        response = edit_tasks(service, request)
        return response.model_dump(mode="json")

    def _tool_search_tasks(self, service: TaskService, params: dict[str, Any]) -> dict[str, Any]:
        request = self._parse_request(SearchTasksRequest, params)
        response = search_tasks(service, request)
        return response.model_dump(mode="json")

    def _tool_get_tasks(self, service: TaskService, params: dict[str, Any]) -> dict[str, Any]:
        request = self._parse_request(GetTasksRequest, params)
        response = get_tasks(service, request)
        return response.model_dump(mode="json")

    @staticmethod
    def _parse_request(model_cls: type[RequestModel], data: dict[str, Any]) -> RequestModel:
        try:
            return model_cls.model_validate(data)
        except ValidationError as exc:
            raise MCPValidationError(str(exc)) from exc
