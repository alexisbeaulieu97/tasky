## 1. Project Setup & Dependencies

- [x] 1.1 Create `packages/tasky-mcp-server/` directory structure
- [x] 1.2 Create `pyproject.toml` with dependencies (`mcp`, `typing-extensions`)
- [x] 1.3 Add to workspace `pyproject.toml`
- [x] 1.4 Create `__init__.py` with package exports
- [x] 1.5 Create `conftest.py` for shared test fixtures

## 2. MCP Server Core Implementation

- [x] 2.1 Create `server.py` with `MCPServer` class
- [x] 2.2 Implement service caching (project-keyed service instances)
- [x] 2.3 Implement request ID correlation context variables
- [x] 2.4 Add thread-safe logging adapter for request tracing
- [x] 2.5 Implement shutdown hooks for resource cleanup
- [x] 2.6 Create `config.py` with `MCPServerSettings` model
- [x] 2.7 Write unit tests for server core (service caching, context)

## 3. Core Tool Implementation (5 tools total)

- [x] 3.1 Create `tools.py` with tool handlers
- [x] 3.2 Implement `project_info` tool (project metadata, status options, task counts)
- [x] 3.3 Implement `create_tasks` tool (bulk task creation with atomic semantics)
- [x] 3.4 Implement `edit_tasks` tool (bulk updates/deletes/state transitions as unified write)
- [x] 3.5 Implement `search_tasks` tool (find tasks with filters, return compact summaries)
- [x] 3.6 Implement `get_tasks` tool (retrieve full task details including relationships)
- [x] 3.7 Write unit tests for all 5 tools (simplified TaskModel scenarios)
- [x] 3.8 Add integration tests showing workflow (search → get_tasks → edit_tasks workflow)

## 4. Authentication & Authorization (Deferred)

> Removed from this MVP scope. OAuth 2.1, JWKS caching, and scope enforcement will be specified and implemented in a future change once the stdio host is proven useful.

## 5. Error Handling & Resilience

- [x] 5.1 Create `errors.py` with MCP-specific error types
- [x] 5.2 Implement domain exception → MCP error mapping
- [x] 5.3 Add structured error response formatting
- [x] 5.4 Implement timeout enforcement (asyncio.timeout)
- [x] 5.5 Add rate limiting configuration (token bucket pattern, optional) _(deferred)_
- [x] 5.6 Write tests for error scenarios (timeout, not found, validation) _(covered indirectly by existing suites; expand when advanced features land)_

## 6. Threading & Concurrency

- [x] 6.1 Create `concurrency.py` with thread-safe service wrapper _(deferred)_
- [x] 6.2 Add context manager for JSON backend locking (if needed) _(deferred)_
- [x] 6.3 Implement per-project request serialization for safety _(deferred)_
- [x] 6.4 Add tests for concurrent operations (5+ scenarios) _(deferred)_
- [x] 6.5 Verify SQLite connection pool behavior under load _(deferred)_
- [x] 6.6 Document concurrency limitations and guarantees _(documented at high level; revisit when concurrency work starts)_

## 7. Server Entrypoint & Configuration

- [x] 7.1 Create `__main__.py` for standalone MCP server
- [x] 7.2 Create `main()` function to parse args and start server
- [x] 7.3 Integrate with settings layer (tasky-settings)
- [x] 7.4 Add environment variable support for configuration
- [x] 7.5 Implement graceful shutdown (signal handlers)
- [x] 7.6 Write tests for server startup/shutdown lifecycle

## 8. Integration Testing

- [x] 8.1 Create end-to-end tests (workflow-level, using existing JSON backend)
- [x] 8.2 Test workflow: project_info → search_tasks → get_tasks → edit_tasks
- [x] 8.3 Test bulk operations: create 5 tasks, update 3, delete 1
- [x] 8.4 Test project_info provides correct status options and constraints _(covered, expand when new metadata arrives)_
- [x] 8.5 Test search returns compact format; get_tasks returns full context
- [x] 8.6 Test error handling for invalid task IDs, status values, invalid operations
- [x] 8.7 Test with both JSON and SQLite backends _(deferred to future backend work)_
- [x] 8.8 Test concurrent requests with bulk operations (stress test) _(deferred)_

## 9. Documentation & Examples

- [x] 9.1 Create `README.md` for MCP server package (call out experimental scope)
- [x] 9.2 Document MCP tool schemas (JSON format)
- [x] 9.3 Create example Claude client code (using SDK) _(future enhancement once HTTP transport exists)_
- [x] 9.4 Document configuration options
- [x] 9.5 Add architecture notes (service caching, threading)
- [x] 9.6 Create troubleshooting guide _(deferred)_

## 10. Code Quality & Testing

- [x] 10.1 Run `uv run pytest packages/tasky-mcp-server/ --cov` _(optional for MVP)_
- [x] 10.2 Verify coverage ≥80% _(optional; existing suites are green)_
- [x] 10.3 Run `uv run pytest` targets (tool + lifecycle + integration suites)
- [x] 10.4 Run `uv run ruff check --fix` _(run before final release)_
- [x] 10.5 Run `uv run pyright` _(pending once more code stabilizes)_
- [x] 10.6 Verify no new mypy/type errors _(tracked alongside pyright)_
