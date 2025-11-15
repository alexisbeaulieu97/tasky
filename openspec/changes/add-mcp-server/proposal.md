# Change: Add MCP Server Integration (Minimal Tool Design)

## Why

Tasky's clean architecture (service layer + storage abstraction + domain models) is ideal for exposing via MCP (Model Context Protocol) to Claude and other AI assistants. Research shows AI agents perform better with fewer, focused tools rather than comprehensive tool sets. An MCP server with minimal focused tools enables:

- Claude to manage tasks effectively with 4 core tools (not 10+)
- AI-assisted task management (summarization, prioritization, automation)
- Integration with Claude's native task understanding
- Stateless, request-based operations (fits MCP model perfectly)

## Design Principle

**Fewer, Better Tools**: 4 focused tools (list, modify, manage, context) with action parameters outperform 10+ individual tools. This reduces decision paralysis and improves Claude's reasoning quality.

## What Changes

- Create `packages/tasky-mcp-server/` - new MCP protocol implementation
- Implement minimal core tools (4 tools total) with unified actions:
  1. `list_tasks` - View tasks with filtering
  2. `modify_task` - Create/update/delete/transition tasks (single tool, multiple actions)
  3. `manage_tasks` - Import/export operations
  4. `context_info` - Project and status information
- Add service caching and connection pooling for long-lived connections
- Implement request-scoped logging with correlation IDs
- Add thread-safe wrappers for JSON backend operations
- Create MCP server startup/shutdown infrastructure
- Add configuration for MCP server (host, port, timeout, concurrency)

## Design Philosophy

**Tool Simplicity Over Completeness**: 4 focused tools with action parameters outperform 10+ individual tools. Claude's decision quality improves with fewer options.

## Impact

- **Affected specs**: New `mcp-integration` spec
- **Affected code**: New package `tasky-mcp-server`, minor extensions to settings
- **Backward compatibility**: Additive only; no breaking changes
- **Dependencies**: Adds `mcp` SDK dependency
- **New capability**: AI assistants can manage tasks via MCP protocol
