## 1. Project Setup & Dependencies

- [ ] 1.1 Create `packages/tasky-mcp-server/` directory structure
- [ ] 1.2 Create `pyproject.toml` with dependencies (`mcp`, `typing-extensions`)
- [ ] 1.3 Add to workspace `pyproject.toml`
- [ ] 1.4 Create `__init__.py` with package exports
- [ ] 1.5 Create `conftest.py` for shared test fixtures

## 2. MCP Server Core Implementation

- [ ] 2.1 Create `server.py` with `MCPServer` class
- [ ] 2.2 Implement service caching (project-keyed service instances)
- [ ] 2.3 Implement request ID correlation context variables
- [ ] 2.4 Add thread-safe logging adapter for request tracing
- [ ] 2.5 Implement shutdown hooks for resource cleanup
- [ ] 2.6 Create `config.py` with `MCPServerSettings` model
- [ ] 2.7 Write unit tests for server core (service caching, context)

## 3. Core Tool Implementation (5 tools total)

- [ ] 3.1 Create `tools.py` with tool handlers
- [ ] 3.2 Implement `project_info` tool (project metadata, status options, task counts)
- [ ] 3.3 Implement `create_tasks` tool (bulk task creation with atomic semantics)
- [ ] 3.4 Implement `edit_tasks` tool (bulk updates/deletes/state transitions as unified write)
- [ ] 3.5 Implement `search_tasks` tool (find tasks with filters, return compact summaries)
- [ ] 3.6 Implement `get_tasks` tool (retrieve full task details including relationships)
- [ ] 3.7 Write unit tests for all 5 tools (40+ test cases covering all operations and bulk paths)
- [ ] 3.8 Add integration tests showing workflow (search → get_tasks → edit_tasks workflow)

## 5. Error Handling & Resilience

- [ ] 5.1 Create `errors.py` with MCP-specific error types
- [ ] 5.2 Implement domain exception → MCP error mapping
- [ ] 5.3 Add structured error response formatting
- [ ] 5.4 Implement timeout enforcement (asyncio.timeout)
- [ ] 5.5 Add rate limiting configuration (token bucket pattern, optional)
- [ ] 5.6 Write tests for error scenarios (timeout, not found, validation)

## 6. Threading & Concurrency

- [ ] 6.1 Create `concurrency.py` with thread-safe service wrapper
- [ ] 6.2 Add context manager for JSON backend locking (if needed)
- [ ] 6.3 Implement per-project request serialization for safety
- [ ] 6.4 Add tests for concurrent operations (5+ scenarios)
- [ ] 6.5 Verify SQLite connection pool behavior under load
- [ ] 6.6 Document concurrency limitations and guarantees

## 7. Server Entrypoint & Configuration

- [ ] 7.1 Create `__main__.py` for standalone MCP server
- [ ] 7.2 Create `main()` function to parse args and start server
- [ ] 7.3 Integrate with settings layer (tasky-settings)
- [ ] 7.4 Add environment variable support for configuration
- [ ] 7.5 Implement graceful shutdown (signal handlers)
- [ ] 7.6 Write tests for server startup/shutdown lifecycle

## 8. Integration Testing

- [ ] 8.1 Create end-to-end tests (full request/response cycle)
- [ ] 8.2 Test workflow: project_info → search_tasks → get_tasks → edit_tasks
- [ ] 8.3 Test bulk operations: create 5 tasks, update 3, delete 1
- [ ] 8.4 Test project_info provides correct status options and constraints
- [ ] 8.5 Test search returns compact format; get_tasks returns full context
- [ ] 8.6 Test error handling for invalid task IDs, status values, invalid operations
- [ ] 8.7 Test with both JSON and SQLite backends
- [ ] 8.8 Test concurrent requests with bulk operations (stress test)

## 9. Documentation & Examples

- [ ] 9.1 Create `README.md` for MCP server package
- [ ] 9.2 Document MCP tool schemas (JSON format)
- [ ] 9.3 Create example Claude client code (using SDK)
- [ ] 9.4 Document configuration options
- [ ] 9.5 Add architecture notes (service caching, threading)
- [ ] 9.6 Create troubleshooting guide

## 10. Code Quality & Testing

- [ ] 10.1 Run `uv run pytest packages/tasky-mcp-server/ --cov`
- [ ] 10.2 Verify coverage ≥80% (currently will be new)
- [ ] 10.3 Run `uv run pytest --cov=packages --cov-fail-under=80`
- [ ] 10.4 Run `uv run ruff check --fix`
- [ ] 10.5 Run `uv run pyright`
- [ ] 10.6 Verify no new mypy/type errors
