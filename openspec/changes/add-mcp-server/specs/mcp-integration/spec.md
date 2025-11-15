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

### Requirement: Minimal Core Tools (4 tools total)

The MCP server SHALL provide ONLY the essential tools Claude needs for practical task management. Tool selection prioritizes decision clarity over feature completeness.

#### Tool 1: `list_tasks` - Unified read operation
- **Parameters**: status (optional), search (optional), created_after (optional)
- **Returns**: Array of task objects sorted by urgency
- **Use case**: Claude reviews task state before acting
- **Handles**: Lists, filters, and searches in one unified tool

#### Tool 2: `modify_task` - Unified write operation
- **Parameters**: task_id (UUID), action (one of: "create", "update", "complete", "cancel", "reopen", "delete")
- **For create**: name, details parameters
- **For update**: optional name, details, priority, due_date parameters
- **For state changes**: only task_id and action parameters
- **Returns**: Updated task object
- **Use case**: Claude performs any task operation with single tool
- **Handles**: CRUD + state transitions

#### Tool 3: `manage_tasks` - Bulk operations
- **Parameters**: action (one of: "import", "export"), format, strategy (for import)
- **Returns**: Operation result with count summary
- **Use case**: Claude manages task datasets
- **Handles**: Import/export in single tool

#### Tool 4: `context_info` - Information retrieval (read-only)
- **Parameters**: query_type (one of: "current_project", "projects", "status_options")
- **Returns**: Metadata (current project, project list, valid statuses)
- **Use case**: Claude understands available context before acting
- **Handles**: Project discovery, enum values, configuration

#### Scenario: Claude manages tasks with 4 focused tools
- **WHEN** Claude wants to create a task
- **THEN** uses `modify_task` with action="create"
- **AND** all CRUD operations use the same tool

#### Scenario: Claude inspects state before acting
- **WHEN** Claude needs to understand what projects/tasks exist
- **THEN** uses `context_info` to understand available options
- **AND** then `list_tasks` to see current state
- **AND** then `modify_task` to make changes

#### Scenario: Claude filters with unified tool
- **WHEN** Claude needs pending urgent tasks
- **THEN** uses `list_tasks` with status="pending" and search="urgent"
- **AND** single tool handles all filtering logic

#### Scenario: Bulk operations are grouped
- **WHEN** Claude imports or exports
- **THEN** uses single `manage_tasks` tool
- **AND** action parameter determines behavior

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
