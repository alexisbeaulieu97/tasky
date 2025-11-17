# Change: Add MCP Server Integration (5 Minimal Tools)

## Why

Tasky's clean architecture (service layer + storage abstraction + domain models) is ideal for exposing via MCP (Model Context Protocol) to Claude and other AI assistants. Research shows AI agents perform better with fewer, focused tools rather than comprehensive tool sets. An MCP server with 5 minimal, purposeful tools enables:

- Claude to manage tasks within a project with high clarity
- AI-assisted task management (summarization, prioritization, automation)
- Integration with Claude's native task understanding
- Stateless, request-based operations (fits MCP model perfectly)
- User control over project context (users manage projects, LLMs manage tasks)

> **Scope update (2025-01-XX):** To ship value incrementally we are constraining this change to a stdio MCP server that exposes the five Tasky tools only. OAuth 2.1, rate limiting, richer metadata (priority/due date, dependencies), and other advanced capabilities will land in future changes.

## Design Principle

**Tool Simplicity Over Completeness**: 5 focused, purposeful tools outperform 10+ individual tools. Each tool has a single, clear responsibility. Users manage projects; Claude manages tasks within assigned project context.

**Search-Inspect-Act Pattern**:
- `search_tasks` returns compact summaries to enable fast filtering
- `get_tasks` returns full task context (descriptions, relationships) only when Claude needs to understand details
- This prevents token waste and creates proper incentives for tool usage

## What Changes

- Create `packages/tasky-mcp-server/` - new MCP protocol implementation
- Implement 5 minimal core tools (users manage projects, Claude manages tasks):
  1. `project_info` - Get project metadata and status options (read-only)
  2. `create_tasks` - Bulk create tasks (one or more)
  3. `edit_tasks` - Bulk edit/update/delete tasks (unified write operation)
  4. `search_tasks` - Find tasks with filters (returns compact format)
  5. `get_tasks` - Retrieve full task details by ID (relationships, descriptions)
- Register the tools with `mcp.Server` and ship a `python -m tasky_mcp_server` stdio host
- Add service caching plus request-scoped logging/trace IDs
- Explicitly defer OAuth, rate limiting, and dependency/deadline metadata to later phases
- Update documentation/tests to reflect the experimental MVP scope

## Design Philosophy

**Minimal Tool Set with Clear Boundaries**: 5 focused tools cover task management completely without overwhelming Claude with choices. Users provide project context at server initialization or per-request; Claude works only within that scope.

**Efficient Information Flow**: Search returns only essential task metadata (id, name, status, due_date, priority). Full context fetched only when needed to prevent token waste and incentivize proper tool usage.

## Impact

- **Affected specs**: New `mcp-integration` spec
- **Affected code**: New package `tasky-mcp-server`, minor extensions to settings
- **Backward compatibility**: Additive only; no breaking changes
- **Dependencies**: Adds `mcp` SDK dependency
- **New capability**: AI assistants can manage tasks via MCP protocol
