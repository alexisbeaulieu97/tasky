# task-filtering-service Specification

## Purpose
TBD - created by archiving change add-task-filtering. Update Purpose after archive.
## Requirements
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

