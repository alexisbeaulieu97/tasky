# Spec: Task Filtering Protocol

**Capability**: `task-filtering-protocol`  
**Status**: Draft  
**Package**: `tasky-tasks`  
**Layer**: Domain

## Overview

Defines the repository protocol extension for status-based task filtering. This specification establishes the contract that all repository implementations must follow when filtering tasks by status.

---

## ADDED Requirements

### Requirement: Repository Protocol Supports Status Filtering

The `TaskRepository` protocol MUST include a method for retrieving tasks filtered by status.

**Rationale**: Enables backend implementations to optimize filtering (e.g., database queries) while maintaining a consistent interface across storage types.

#### Scenario: Get tasks by specific status

**Given** a `TaskRepository` protocol definition  
**When** the protocol is examined  
**Then** it MUST include a `get_tasks_by_status(status: TaskStatus) -> list[TaskModel]` method signature  
**And** the method MUST accept a `TaskStatus` enum value as parameter  
**And** the method MUST return a list of `TaskModel` instances  
**And** the method signature MUST use type hints for all parameters and return values

#### Scenario: Protocol documentation explains filtering behavior

**Given** the `get_tasks_by_status` method in the protocol  
**When** a developer reviews the protocol definition  
**Then** the method MUST include a docstring  
**And** the docstring MUST explain that only tasks matching the specified status are returned  
**And** the docstring MUST clarify that an empty list is returned when no tasks match

#### Scenario: Protocol maintains backward compatibility

**Given** existing `TaskRepository` implementations  
**When** the protocol is extended with `get_tasks_by_status`  
**Then** existing protocol methods (`get_all_tasks`, `save_task`, etc.) MUST remain unchanged  
**And** the protocol MUST NOT introduce breaking changes to existing method signatures

---

## Implementation Notes

- Method signature: `def get_tasks_by_status(self, status: TaskStatus) -> list[TaskModel]: ...`
- Located in: `packages/tasky-tasks/src/tasky_tasks/ports.py`
- Import `TaskStatus` from `tasky_tasks.models` in TYPE_CHECKING block
- Follows existing protocol conventions (return type hints, docstring format)

---

## Testing Requirements

- Protocol type-checks successfully with mypy/pyright
- No runtime tests needed (Protocol is interface-only)
- Implementations will be tested separately

---

## Related Specifications

- `task-filtering-json-backend`: JSON implementation of this protocol
- `task-filtering-service`: Service layer using this protocol
