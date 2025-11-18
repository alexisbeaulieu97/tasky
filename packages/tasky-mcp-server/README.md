# tasky-mcp-server

Model Context Protocol (MCP) server for Tasky task management.

## Overview

`tasky-mcp-server` exposes Tasky's task management capabilities through the [Model Context Protocol](https://modelcontextprotocol.io/), enabling AI assistants like Claude to interact with your task projects. The server provides a unified interface for task creation, editing, searching, and project introspection.

## Status

> **Phase 1 stdio MVP:** The server implements all 5 core MCP tools over stdio transport with service caching, request tracing, and graceful shutdown. OAuth 2.1, HTTP transport, and advanced concurrency controls are deferred to future phases. **Note:** JSON backend has known concurrency limitations (see Threading Model section) - use SQLite for multi-user scenarios.

## Features

- **5 Core Tools**: Complete task lifecycle management
  - `project_info`: Project metadata, status options, and task counts
  - `create_tasks`: Bulk task creation with atomic semantics
  - `edit_tasks`: Unified write interface for updates, deletes, and state transitions
  - `search_tasks`: Find tasks with filters, return compact summaries
  - `get_tasks`: Retrieve full task details with relationships
  - _Current implementation works with today’s TaskModel fields (name, details, status, timestamps). Priority, due dates, and dependency graphs will be wired in as the domain evolves._
  
- **Service Caching**: Project-keyed service instances avoid re-initialization
- **Request Tracing**: Correlation IDs for debugging multi-step workflows
- **Graceful Shutdown**: Resource cleanup hooks ensure proper termination
- **Thread-Safe**: RLock-protected service cache for concurrent access
- **Timeout Enforcement**: Configurable timeouts prevent hanging operations

## Current Limitations

- MCP transport wiring is still a skeleton; the entry point currently exposes lifecycle hooks without binding to HTTP/stdio.
- OAuth 2.1 / RFC 8707 validation, scope enforcement, and rate limiting are not implemented yet.
- Tool schemas only expose the data available on the current TaskModel; richer metadata (priority, due dates, dependencies) is planned.
- Concurrency controls (`max_concurrent_requests`, storage locking helpers) are defined at the config level but not yet enforced.

## Installation

```bash
# Install from workspace root
uv sync

# Or install package directly
cd packages/tasky-mcp-server
uv pip install -e .
```

## Quick Start

### 1. Initialize a Tasky Project

```bash
# Create a project directory
mkdir my-project && cd my-project

# Initialize Tasky project
uv run tasky project init

# Create some tasks
uv run tasky tasks create "Review PRs" "Check open pull requests"
uv run tasky tasks create "Update docs" "Document new API endpoints"
```

### 2. Start the MCP Server

```bash
# Start server on stdio (host/port retained for future transports)
uv run python -m tasky_mcp_server

# Or specify custom configuration
uv run python -m tasky_mcp_server \
  --host 0.0.0.0 \
  --port 9000 \
  --project-path /path/to/project \
  --timeout-seconds 120 \
  --max-concurrent-requests 20 \
  --debug
```

## Tool Schemas

### project_info

Get project metadata, available status options, and task counts.

**Request:** `{}`

**Response:**
```json
{
  "project_name": "my-project",
  "project_description": "Project description",
  "project_path": "/Users/alice/my-project",
  "available_statuses": ["pending", "completed", "cancelled"],
  "task_counts": {"pending": 6, "completed": 3, "cancelled": 1}
}
```

### create_tasks

Create one or more tasks atomically. All succeed or all fail.

**Request:**
```json
{
  "tasks": [
    {"name": "Review PRs", "details": "Check open pull requests"},
    {"name": "Update docs", "details": "Document new API endpoints"}
  ]
}
```

### edit_tasks

Unified write interface for updates, deletes, and state transitions.

**Request:**
```json
{
  "operations": [
    {"task_id": "...", "action": "update", "name": "New name"},
    {"task_id": "...", "action": "complete"},
    {"task_id": "...", "action": "delete"}
  ]
}
```

### search_tasks

Find tasks with filters. Supports status, substring, and created-after filters.

**Request:**
```json
{
  "status": "pending",
  "search": "review",
  "created_after": "2025-01-01T00:00:00+00:00",
  "limit": 25,
  "offset": 0
}
```

**Response:**
```json
{
  "tasks": [
    {"task_id": "task-uuid-1", "name": "Review PRs", "status": "pending"},
    {"task_id": "task-uuid-2", "name": "Review onboarding docs", "status": "pending"}
  ],
  "total_count": 2
}
```

### get_tasks

Retrieve full task details by ID.

**Request:**
```json
{
  "task_ids": ["task-uuid-1", "task-uuid-2"]
}
```

**Response:**
```json
[
  {
    "task_id": "task-uuid-1",
    "name": "Review PRs",
    "details": "Check open pull requests",
    "status": "pending",
    "created_at": "2025-01-05T12:00:00+00:00",
    "updated_at": "2025-01-05T12:00:00+00:00"
  }
]
```

## Configuration

### Environment Variables

```bash
TASKY_MCP_HOST=0.0.0.0              # Server host (default: 127.0.0.1)
TASKY_MCP_PORT=9000                  # Server port (default: 8080)
TASKY_MCP_TIMEOUT_SECONDS=120        # Request timeout (default: 60)
TASKY_MCP_MAX_CONCURRENT_REQUESTS=20 # Max concurrent requests (default: 10)
TASKY_MCP_PROJECT_PATH=/path/to/project  # Project path (auto-detects if not specified)
```

### Command-Line Arguments

```bash
uv run python -m tasky_mcp_server \
  --host 0.0.0.0 \
  --port 9000 \
  --project-path /path/to/project \
  --debug
```

## Architecture

### Service Caching

The server maintains a cache of `TaskService` instances keyed by project path. This avoids re-initialization overhead and ensures consistent service state across requests.

### Request Tracing

Each request gets a unique correlation ID stored in a context variable. The logging adapter automatically includes this ID in all log messages for debugging multi-step workflows.

### Threading Model and Concurrency

The server implements concurrency controls with the following guarantees:

- **Service cache**: Protected by `threading.RLock` for concurrent access
- **Request isolation**: Each request gets its own context and correlation ID
- **Concurrent request limiting**: Semaphore caps concurrent requests (default: 10, configurable via `max_concurrent_requests`)

**Known Limitations (Phase 1 - stdio MVP):**

⚠️ **JSON Backend Concurrency**: The JSON backend is **not fully thread-safe for concurrent edits to the same project**. While the server limits concurrent requests via semaphore, concurrent operations within a single request window can experience race conditions:
- Multiple concurrent requests to the same project may result in lost updates
- Last-write-wins semantics apply (no optimistic locking or conflict detection)
- Corruption risk is low for typical single-user stdio usage but increases with concurrent access

**Recommendations:**
- For single-user stdio scenarios (Phase 1 target), the risk is minimal
- For multi-user or HTTP transport scenarios, use SQLite backend instead of JSON
- Future phases will add per-project request serialization and optimistic locking

**SQLite Backend**: Connection pooling ensures thread-safe concurrent access with proper transaction isolation.

### Graceful Shutdown

The server supports registering shutdown hooks for cleanup. All hooks are executed on shutdown, and the service cache is cleared.

## Error Handling

The server maps domain exceptions to MCP-specific errors:

- Validation and parsing issues → `MCPValidationError`
- Project/service discovery issues → `MCPError`
- Timeout enforcement → `MCPTimeoutError`

Future iterations will expand this table with OAuth and concurrency-specific failures.

## Development

```bash
# Run tests
uv run pytest tests/test_integration.py tests/test_lifecycle.py -v

# Run with coverage
uv run pytest tests/ --cov=src --cov-report=html

# Lint and auto-fix
uv run ruff check --fix

# Type checking
uv run pyright src/
```

## License

MIT License - see LICENSE file in repository root.
