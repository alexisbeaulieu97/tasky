# mcp-integration Specification

## Purpose
TBD - created by archiving change add-mcp-server. Update Purpose after archive.
## Requirements
### Requirement: MCP Server Implementation

The system SHALL provide an MCP (Model Context Protocol) server that exposes Tasky functionality for use by Claude and other AI assistants. Phase 1 targets a stdio transport with the five core tools wired into `mcp.Server`; the server stays stateless/request-based and reuses the existing TaskService per project. Future transports (HTTP/WebSocket) remain out of scope for this phase.

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

### Requirement: Minimal Core Tools (5 tools total)

The MCP server SHALL provide ONLY the essential tools Claude needs for practical task management. Tool selection prioritizes decision clarity over feature completeness. Users manage projects; Claude manages tasks within assigned project context.

#### Tool 1: `project_info` - Get project context (read-only)
- **Purpose**: Let Claude understand the current project scope
- **Parameters**: None (project context provided by server configuration)
- **Returns**: Project name, description, available status values, task counts by status
- **Use case**: Claude queries available statuses before filtering/creating
- **Note**: Single source of truth for valid task statuses and project scope

#### Tool 2: `create_tasks` - Bulk task creation
- **Purpose**: Create one or more tasks in a single operation
- **Parameters**: Array of task specifications (each with name, details, priority, due_date)
- **Returns**: Array of created TaskModel objects with IDs and timestamps
- **Bulk semantics**: All tasks created atomically; partial failure returns error with details
- **Use case**: Claude creates multiple tasks or single task (wrapped in array)
- **Handles**: Task creation with optional metadata

#### Tool 3: `edit_tasks` - Bulk task editing (unified write)
- **Purpose**: Update, delete, or transition tasks in a single operation
- **Parameters**: Array of edit operations (each with task_id, action, optional updates)
- **Actions**: "update" (modify fields), "delete" (hard-delete permanent removal), "complete" (mark done), "cancel" (cancel), "reopen" (reopen completed)
- **For update action**: optional name, details, priority, due_date, status
- **For state actions**: only task_id and action required
- **Returns**: Array of updated TaskModel objects
- **Bulk semantics**: All edits applied atomically; partial failure returns error with details
- **Use case**: Claude modifies multiple tasks or single task (wrapped in array)
- **Design**: Unified write operation like database transaction
- **Delete semantics (hard-delete)**:
  - Deletion is permanent and irreversible (no recovery mechanism)
  - Deleted tasks are immediately removed from all queries/listings
  - Deletion events are recorded in audit logs (if enabled via Phase 10 advanced backends)
  - Audit trail records: actor=mcp_server, timestamp=operation_time, action=delete, task_id, reason=provided_by_client
  - Soft-delete (archival/hidden status) is not supported in Phase 8; if non-destructive deletion is needed, use status="archived" or similar via update action
  - Return value on delete: TaskModel with deletion_confirmed=true flag, or error if task not found

#### Tool 4: `search_tasks` - Find tasks with compact results
- **Purpose**: Fast filtered search to identify relevant tasks
- **Parameters**: status (optional), search (optional text), created_after (optional date), due_before (optional date)
- **Returns**: Array of compact task summaries (task_id, name, status)
- **Compact format**: task_id, name, status only (other metadata deferred until the domain publishes it)
- **Use case**: Claude discovers which tasks match criteria before inspecting details
- **Design**: Returns minimal data to prevent token waste; Claude uses get_tasks for deep inspection

#### Tool 5: `get_tasks` - Retrieve full task details
- **Purpose**: Retrieve complete task information including relationships
- **Parameters**: Array of task IDs
- **Returns**: Array of full TaskModel objects with all fields, blockers, blocked_by, subtasks, subtask_of
- **Use case**: Claude needs to understand task dependencies, detailed description, or relationships
- **Design**: Fetched selectively after search; only when Claude needs to "do the work"
- **Relationships**: Includes full graph of task dependencies for complex planning

#### Scenario: Claude manages multiple related tasks
- **WHEN** Claude searches for "pending urgent" tasks
- **THEN** uses `search_tasks` with status="pending" and search="urgent"
- **AND** receives compact list (id, name, status, due_date, priority)
- **AND** Claude identifies 3 relevant tasks to work on

#### Scenario: Claude understands task complexity before acting
- **WHEN** Claude needs to understand blockers and subtasks
- **THEN** uses `get_tasks` with the identified task IDs
- **AND** receives full context including dependencies and descriptions
- **AND** Claude can now make informed decisions about task ordering

#### Scenario: Claude creates multiple tasks
- **WHEN** Claude needs to create 5 related tasks
- **THEN** uses `create_tasks` with array of 5 task specs
- **AND** all 5 are created atomically
- **AND** receives created tasks with IDs and timestamps

#### Scenario: Claude modifies multiple tasks atomically
- **WHEN** Claude needs to update priorities for 3 tasks and complete 1 task
- **THEN** uses `edit_tasks` with array of 4 operations
- **AND** operations: {id, action="update", priority=1}, {id, action="update", priority=2}, {id, action="update", priority=3}, {id, action="complete"}
- **AND** all edits applied atomically
- **AND** receives updated tasks

#### Scenario: Claude respects project scope
- **WHEN** Claude starts managing a project
- **THEN** calls `project_info` first to understand valid statuses
- **AND** only uses statuses returned by `project_info`
- **AND** project context is validated by server (not by Claude)

### Requirement: Error Handling & Reliability

The MCP server SHALL handle errors gracefully and provide clear error messages. For Phase 1 the server reuses existing Tasky validation plus the new MCP error helpers; rate limiting and per-backend concurrency controls remain deferred.

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

#### Scenario: Concurrent operations are handled safely _(Deferred)_
- **WHEN** multiple MCP requests arrive simultaneously
- **THEN** all are processed correctly (no data corruption)
- **AND** JSON backend operations are serialized (thread-safe)
- **AND** SQLite operations use connection pooling
- **AND** no deadlocks occur

### Requirement: Authentication & Authorization _(Deferred)_

Full OAuth 2.1 / RFC 8707 compliance is out of scope for the stdio MVP. When the HTTP transport lands, the server SHALL implement token validation, resource indicators, and scope enforcement per this section. Until then, the server assumes trust in the local CLI/stdio connection.

#### Scenario: Server implements OAuth 2.1 compliance
- **GIVEN** MCP server configured with HTTP transport (host="0.0.0.0", port=9000)
- **WHEN** clients establish MCP connections
- **THEN** server requires OAuth 2.1 authorization
- **AND** clients MUST present valid access tokens
- **AND** server validates token scope and resource binding

#### Scenario: Resource Indicators (RFC 8707) bind tokens to server URI
- **GIVEN** a client requests authorization from OAuth 2.1 provider
- **WHEN** client includes Resource Indicator in token request (e.g., `resource=https://localhost:9000/mcp`)
- **THEN** issued token is bound to the MCP server resource
- **AND** token cannot be used against other MCP servers or resources (prevents token misuse)
- **AND** server validates resource_aud claim in token matches expected URI

#### Scenario: Client authentication validation
- **GIVEN** incoming MCP request
- **WHEN** request includes Authorization header with Bearer token
- **THEN** server extracts and validates token signature and expiry
- **AND** server verifies token claims (sub, aud, resource_aud, scopes)
- **AND** invalid/expired tokens are rejected with 401 Unauthorized

#### Scenario: Token scope enforcement
- **GIVEN** validated OAuth token with scopes (e.g., "tasks:read tasks:write projects:read")
- **WHEN** client attempts operation (create_tasks, edit_tasks, search_tasks)
- **THEN** server checks if token has required scope for operation
- **AND** operations requiring write access require "tasks:write" scope
- **AND** operations requiring project access require "projects:read" scope
- **AND** insufficient scope returns 403 Forbidden with "insufficient_scope" error

#### Scenario: Access control per project/task (future authorization model)
- **GIVEN** multi-project or multi-user scenario (Phase 10+)
- **WHEN** client token includes project_id claims
- **THEN** server limits operations to authorized projects only
- **AND** token may specify read-only vs read-write access per project
- **AND** cross-project operations are blocked if not authorized

#### Scenario: Configuration for OAuth provider
- **GIVEN** MCP server startup
- **WHEN** environment variables specify `OAUTH_ISSUER_URL`, `OAUTH_CLIENT_ID`, `OAUTH_AUDIENCE`
- **THEN** server fetches JWKS from OAuth provider
- **AND** validates incoming tokens against provider's public keys
- **AND** caches JWKS with TTL to reduce provider calls

### Requirement: MCP Server Configuration

The MCP server SHALL be configurable via environment variables or configuration files (via `AppSettings.mcp`). Host/port knobs are placeholders for future transports but remain harmless defaults for the stdio host.

#### Scenario: Server can be customized
- **GIVEN** MCP server startup
- **WHEN** configuration specifies host="0.0.0.0", port=9000, timeout_seconds=60
- **THEN** server listens on specified host and port
- **AND** operations timeout after 60 seconds
- **AND** max concurrent requests limit is enforced

#### Scenario: Server can be started standalone (stdio MVP)
- **WHEN** running `python -m tasky_mcp_server`
- **THEN** server starts on configured address
- **AND** is ready to accept MCP connections
- **AND** logs indicate successful startup
- **AND** graceful shutdown is supported (SIGTERM, SIGINT)

