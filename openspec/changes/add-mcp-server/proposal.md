# Change: Add MCP Server Integration

## Why

Tasky's clean architecture (service layer + storage abstraction + domain models) is ideal for exposing via MCP (Model Context Protocol) to Claude and other AI assistants. Currently, users can only interact with tasks through the CLI. An MCP server enables:

- Claude to read/write tasks directly on behalf of users
- AI-assisted task management (summarization, prioritization, automation)
- Integration with Claude's native task understanding
- Stateless, request-based operations (fits MCP model perfectly)

## What Changes

- Create `packages/tasky-mcp-server/` - new MCP protocol implementation
- Implement MCP tools for task and project operations (10+ tools)
- Add service caching and connection pooling for long-lived connections
- Implement request-scoped logging with correlation IDs
- Add thread-safe wrappers for JSON backend operations
- Create MCP server startup/shutdown infrastructure
- Add configuration for MCP server (host, port, timeout, concurrency)

## Impact

- **Affected specs**: New `mcp-integration` spec
- **Affected code**: New package `tasky-mcp-server`, minor extensions to settings
- **Backward compatibility**: Additive only; no breaking changes
- **Dependencies**: Adds `mcp` SDK dependency
- **New capability**: AI assistants can manage tasks via MCP protocol
