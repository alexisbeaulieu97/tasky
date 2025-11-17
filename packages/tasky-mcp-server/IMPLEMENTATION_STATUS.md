# MCP Server Implementation Status

## Summary

Status: **Foundational work complete; major spec items still pending.** The package now provides Tasky-facing MCP tools, configuration plumbing (including `AppSettings.mcp`), and truthful documentation/tests, but it intentionally leaves the MCP transport bindings, OAuth 2.1 enforcement, rate limiting, and concurrency guarantees unfinished.

## What Works Today

- Core tool handlers (`project_info`, `create_tasks`, `edit_tasks`, `search_tasks`, `get_tasks`) operate on the current TaskModel (name/details/status/timestamps) and are exercised via `tests/test_tools.py` and `tests/test_integration.py`.
- `MCPServer` implements service caching, request ID correlation, shutdown hooks, and timeout helpers, with unit coverage in `tests/test_server.py` and lifecycle scenarios in `tests/test_lifecycle.py`.
- Configuration is centralized: `tasky_settings.AppSettings` now exposes an `mcp: MCPServerSettings` section so hosts can load MCP config through the standard settings graph.
- Documentation (README) clearly calls out the experimental nature of the server and reflects the actual request/response schemas that exist today.

## Still Missing / Planned

- **Transport binding:** `__main__.py` exposes lifecycle hooks but does not yet wire HTTP or stdio transports or register tool handlers with `mcp.Server`.
- **OAuth 2.1 & RFC 8707:** Token validation, JWKS fetching, scope enforcement, and `resource_aud` checks remain to be implemented.
- **Concurrency & rate limiting:** `max_concurrent_requests`, JSON locking helpers, and token-bucket rate limiting are not enforced.
- **Extended schemas:** Priority, due dates, pagination, and dependency graphs await future domain changes.
- **End-to-end stress/integration tests:** No automated suite currently exercises real MCP client/server interactions.

## Test Status (current run targets)

```
uv run pytest packages/tasky-mcp-server/tests/test_server.py \
               packages/tasky-mcp-server/tests/test_lifecycle.py \
               packages/tasky-mcp-server/tests/test_tools.py \
               packages/tasky-mcp-server/tests/test_integration.py
```

All of the above pass against the simplified tool contract. Removed legacy tests that expected nonexistent TaskModel fields (priority/due_date).

## Next Steps

1. Implement OAuth/authz module plus JWKS caching and scope enforcement.
2. Wire up the MCP transport (stdio/HTTP) and register the five tools directly on the `mcp.Server` instance.
3. Enforce concurrency limits and add rate limiting + storage locking helpers.
4. Extend tool schemas once the underlying domain supports richer metadata.
5. Add end-to-end tests that run over the real MCP protocol and capture regression coverage.
