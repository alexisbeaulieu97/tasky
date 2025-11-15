## ADDED Requirements

### Requirement: MCP Server Implementation

The system SHALL provide an MCP (Model Context Protocol) server that exposes Tasky functionality for use by Claude and other AI assistants. The server SHALL be stateless, request-based, and thread-safe.

#### Scenario: Claude creates a task via MCP
- **WHEN** Claude calls the `create_task` MCP tool with name="Buy groceries", details="Milk, eggs"
- **THEN** the tool is processed and a new task is created
- **AND** a TaskModel is returned with task_id, status, timestamps
- **AND** the task is persisted to the configured backend (JSON or SQLite)

#### Scenario: Claude lists tasks with filters via MCP
- **WHEN** Claude calls `list_tasks` with status="pending" and search="urgent"
- **THEN** all pending tasks matching the search term are returned
- **AND** results are sorted and formatted for readability
- **AND** pagination parameters are respected (if large result set)

#### Scenario: Service instances are cached per-project
- **WHEN** multiple MCP tool calls reference the same project
- **THEN** the same service instance is reused (not recreated)
- **AND** subsequent calls are faster (no re-initialization)
- **AND** state from previous calls is available (e.g., open cursors, connections)

#### Scenario: Request IDs enable tracing
- **WHEN** an MCP request is processed
- **THEN** a unique request ID is assigned
- **AND** all log entries for that request include the request ID
- **AND** if an error occurs, the request ID is included in the error response
- **AND** developers can trace full request flow in logs

### Requirement: Task Operation Tools

The MCP server SHALL provide tools for all task operations: create, read, update, delete, list, filter, status transitions, import, export.

#### Scenario: All task CRUD operations work
- **WHEN** Claude uses create_task, get_task, update_task, delete_task
- **THEN** all operations work identically to CLI commands
- **AND** error handling is consistent (same exception types)
- **AND** validation rules are identical
- **AND** state transitions are enforced (can't complete already-completed task)

#### Scenario: Filtering works through MCP
- **WHEN** Claude calls `list_tasks` with combined filters (status + search + date range)
- **THEN** results are filtered correctly
- **AND** filter behavior matches CLI implementation
- **AND** large result sets are handled efficiently

#### Scenario: Import/export work through MCP
- **WHEN** Claude imports tasks via MCP with file content and strategy
- **THEN** tasks are imported (merge, skip, or replace strategy)
- **AND** import result includes count of imported/skipped tasks
- **AND** error cases (malformed file, conflicts) are handled

### Requirement: Project Management Tools

The MCP server SHALL provide tools for project discovery, switching, and initialization.

#### Scenario: Claude can list available projects
- **WHEN** Claude calls `list_projects`
- **THEN** all registered projects are returned with metadata
- **AND** pagination is applied for large registries
- **AND** current project is indicated

#### Scenario: Claude can switch projects
- **WHEN** Claude calls `switch_project` with project name or path
- **THEN** the current project is switched
- **AND** subsequent operations work in the new project context
- **AND** error is returned if project doesn't exist

### Requirement: Error Handling & Reliability

The MCP server SHALL handle errors gracefully, provide clear error messages, and enforce resource limits.

#### Scenario: Invalid input is rejected with clear error
- **WHEN** Claude provides invalid input (bad UUID, invalid status value)
- **THEN** error is returned with code (e.g., "validation_error")
- **AND** error message explains the problem
- **AND** suggestions are provided (valid statuses, date format)

#### Scenario: Operations timeout if taking too long
- **WHEN** an operation (import, discovery, query) exceeds timeout
- **THEN** operation is cancelled and error is returned
- **AND** error message indicates timeout (not generic failure)
- **AND** resources are cleaned up

#### Scenario: Concurrent operations are handled safely
- **WHEN** multiple MCP requests arrive simultaneously
- **THEN** all are processed correctly (no data corruption)
- **AND** JSON backend operations are serialized (thread-safe)
- **AND** SQLite operations use connection pooling
- **AND** no deadlocks occur

### Requirement: MCP Server Configuration

The MCP server SHALL be configurable via environment variables or configuration files.

#### Scenario: Server can be customized
- **GIVEN** MCP server startup
- **WHEN** configuration specifies host="0.0.0.0", port=9000, timeout_seconds=60
- **THEN** server listens on specified host and port
- **AND** operations timeout after 60 seconds
- **AND** max concurrent requests limit is enforced

#### Scenario: Server can be started standalone
- **WHEN** running `python -m tasky_mcp_server`
- **THEN** server starts on configured address
- **AND** is ready to accept MCP connections
- **AND** logs indicate successful startup
- **AND** graceful shutdown is supported (SIGTERM, SIGINT)
