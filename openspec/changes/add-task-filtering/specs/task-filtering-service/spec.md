# Spec: Task Filtering Service Methods

**Capability**: `task-filtering-service`  
**Status**: Draft  
**Package**: `tasky-tasks`  
**Layer**: Domain

## Overview

Extends the `TaskService` class with methods for retrieving filtered task subsets by status. Provides both a general filtering method and convenience methods for common status queries.

---

## ADDED Requirements

### Requirement: Service Delegates Status Filtering to Repository

The `TaskService` MUST provide a method that delegates status-based filtering to the repository layer.

**Rationale**: Maintains separation of concerns—service orchestrates operations while repository handles data access and filtering logic.

#### Scenario: Get tasks by status delegates to repository

**Given** a `TaskService` instance with a configured repository  
**And** the repository contains tasks with various statuses  
**When** `service.get_tasks_by_status(TaskStatus.PENDING)` is called  
**Then** the service MUST call `repository.get_tasks_by_status(TaskStatus.PENDING)`  
**And** the service MUST return the list of tasks returned by the repository  
**And** the service MUST NOT modify or filter the repository result

#### Scenario: Service handles empty filter results

**Given** a `TaskService` instance  
**And** the repository contains no tasks matching the requested status  
**When** `service.get_tasks_by_status(status)` is called  
**Then** the service MUST return an empty list  
**And** the service MUST NOT raise an exception

---

### Requirement: Service Provides Convenience Methods for Common Filters

The `TaskService` MUST provide dedicated methods for the three standard task statuses to simplify common operations.

**Rationale**: Reduces code duplication and improves readability in CLI and other consumers. Ensures consistent status value usage.

#### Scenario: Get pending tasks

**Given** a `TaskService` instance  
**When** `service.get_pending_tasks()` is called  
**Then** the service MUST call `self.get_tasks_by_status(TaskStatus.PENDING)`  
**And** the service MUST return only tasks with `status == TaskStatus.PENDING`

#### Scenario: Get completed tasks

**Given** a `TaskService` instance  
**When** `service.get_completed_tasks()` is called  
**Then** the service MUST call `self.get_tasks_by_status(TaskStatus.COMPLETED)`  
**And** the service MUST return only tasks with `status == TaskStatus.COMPLETED`

#### Scenario: Get cancelled tasks

**Given** a `TaskService` instance  
**When** `service.get_cancelled_tasks()` is called  
**Then** the service MUST call `self.get_tasks_by_status(TaskStatus.CANCELLED)`  
**And** the service MUST return only tasks with `status == TaskStatus.CANCELLED`

#### Scenario: Convenience methods are consistent

**Given** a repository with mixed task statuses  
**When** all three convenience methods are called  
**Then** the union of returned tasks MUST equal `service.get_all_tasks()`  
**And** no task MUST appear in more than one result set  
**And** the total count across all methods MUST match the total task count

---

## Implementation Notes

- Add to: `packages/tasky-tasks/src/tasky_tasks/service.py`
- Method signatures:
  - `def get_tasks_by_status(self, status: TaskStatus) -> list[TaskModel]:`
  - `def get_pending_tasks(self) -> list[TaskModel]:`
  - `def get_completed_tasks(self) -> list[TaskModel]:`
  - `def get_cancelled_tasks(self) -> list[TaskModel]:`
- Import `TaskStatus` from `tasky_tasks.models`
- Include docstrings for each method

---

## Testing Requirements

- Unit test filtering with mock repository
- Verify each convenience method calls correct status
- Test empty result handling
- Verify no exceptions on empty repositories
- Confirm convenience methods return disjoint sets

**Test File**: `packages/tasky-tasks/tests/test_filtering.py`

**Test Cases**:
1. `test_get_tasks_by_status_delegates_to_repository`
2. `test_get_tasks_by_status_returns_empty_list_when_no_matches`
3. `test_get_pending_tasks_calls_correct_status`
4. `test_get_completed_tasks_calls_correct_status`
5. `test_get_cancelled_tasks_calls_correct_status`
6. `test_convenience_methods_partition_all_tasks`

---

## Related Specifications

- `task-filtering-protocol`: Protocol this service uses
- `task-filtering-json-backend`: Backend implementation
- `task-filtering-cli`: CLI consumer of these methods
