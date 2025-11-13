# task-filtering-json-backend Specification

## Purpose
TBD - created by archiving change add-task-filtering. Update Purpose after archive.
## Requirements
### Requirement: JSON Repository Filters Tasks by Status In-Memory

The `JsonTaskRepository` MUST implement the `get_tasks_by_status` protocol method using in-memory filtering.

**Rationale**: JSON backend has no query optimization capabilities, so in-memory filtering is the appropriate approach. This establishes a baseline implementation that future database backends can optimize.

#### Scenario: Filter tasks by status from populated repository

**Given** a `JsonTaskRepository` with tasks having various statuses  
**And** the repository contains at least one task with `status == TaskStatus.PENDING`  
**When** `repository.get_tasks_by_status(TaskStatus.PENDING)` is called  
**Then** the repository MUST return a list containing only tasks with `status == TaskStatus.PENDING`  
**And** the returned tasks MUST be `TaskModel` instances  
**And** all other task data (name, details, created_at, etc.) MUST be preserved correctly

#### Scenario: Filter returns empty list when no matches exist

**Given** a `JsonTaskRepository` with tasks  
**And** no tasks have `status == TaskStatus.CANCELLED`  
**When** `repository.get_tasks_by_status(TaskStatus.CANCELLED)` is called  
**Then** the repository MUST return an empty list  
**And** the repository MUST NOT raise an exception

#### Scenario: Filter handles non-existent document gracefully

**Given** a `JsonTaskRepository` where the storage file does not exist  
**When** `repository.get_tasks_by_status(any_status)` is called  
**Then** the repository MUST return an empty list  
**And** the repository MUST NOT raise a `StorageDataError`  
**And** the repository MUST NOT create the storage file

#### Scenario: Filter preserves task data integrity

**Given** a `JsonTaskRepository` with tasks containing all TaskStatus values  
**When** filtering by each status and comparing to original tasks  
**Then** filtered tasks MUST have identical `task_id`, `name`, `details`, `created_at`, `updated_at`  
**And** task data MUST NOT be mutated during filtering  
**And** each task MUST appear in exactly one filtered result

#### Scenario: Filter handles malformed data correctly

**Given** a `JsonTaskRepository` where task snapshot has invalid status value  
**When** `repository.get_tasks_by_status(TaskStatus.PENDING)` is called  
**Then** the repository MUST skip tasks with invalid status  
**Or** the repository MUST raise `StorageDataError` with clear message  
**And** valid tasks MUST still be returned in the result

---

### Requirement: JSON Repository Filtering is Performant for Typical Workloads

The filtering implementation MUST perform acceptably for repositories with thousands of tasks.

**Rationale**: In-memory filtering has O(n) complexity. Acceptable performance (under 100ms) for typical task counts (<10,000 tasks) ensures good user experience.

#### Scenario: Filter completes quickly for large task count

**Given** a `JsonTaskRepository` with 5,000 tasks  
**And** tasks are evenly distributed across all statuses  
**When** `repository.get_tasks_by_status(TaskStatus.PENDING)` is called  
**Then** the operation MUST complete in under 100 milliseconds  
**And** memory usage MUST remain reasonable (< 50MB additional)

---

