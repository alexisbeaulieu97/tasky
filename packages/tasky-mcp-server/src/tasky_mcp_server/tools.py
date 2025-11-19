"""MCP tools for task management.

This module implements the 5 core MCP tools:
1. project_info - Get project metadata and status options
2. create_tasks - Bulk create tasks
3. edit_tasks - Bulk edit/update/delete tasks
4. search_tasks - Find tasks with filters (compact format)
5. get_tasks - Retrieve full task details by ID
"""

from __future__ import annotations

import logging
import tomllib
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, NoReturn
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from tasky_tasks.enums import TaskStatus
from tasky_tasks.models import TaskModel

from tasky_mcp_server.errors import MCPValidationError

if TYPE_CHECKING:
    from tasky_tasks.service import TaskService

logger = logging.getLogger(__name__)


# ========== Tool Request/Response Models ==========


class ProjectInfoRequest(BaseModel):
    """Request for project_info tool."""

    model_config = ConfigDict(extra="forbid")


class ProjectInfoResponse(BaseModel):
    """Response for project_info tool."""

    project_name: str = Field(description="Name of the project")
    project_description: str = Field(description="Description of the project")
    project_path: str = Field(description="Path to the project")
    available_statuses: list[str] = Field(
        description="Valid task status values",
    )
    task_counts: dict[str, int] = Field(
        description="Count of tasks by status",
    )


class TaskCreateSpec(BaseModel):
    """Specification for creating a task."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., description="Task name")
    details: str | None = Field(None, description="Task details")


class CreateTasksRequest(BaseModel):
    """Request for create_tasks tool."""

    model_config = ConfigDict(extra="forbid")

    tasks: list[TaskCreateSpec] = Field(
        description="List of tasks to create",
        min_length=1,
    )


class CreateTasksResponse(BaseModel):
    """Response for create_tasks tool."""

    created: list[TaskModel] = Field(
        description="Created tasks with IDs and timestamps",
    )


class EditTaskOperation(BaseModel):
    """Single edit operation for a task."""

    model_config = ConfigDict(extra="forbid")

    task_id: str = Field(description="UUID of the task to edit")
    action: str = Field(
        description="Action: 'update', 'delete', 'complete', 'cancel', 'reopen'",
    )
    name: str | None = Field(default=None, description="New task name (update only)")
    details: str | None = Field(
        default=None,
        description="New task details (update only)",
    )


class EditTasksRequest(BaseModel):
    """Request for edit_tasks tool."""

    model_config = ConfigDict(extra="forbid")

    operations: list[EditTaskOperation] = Field(
        description="List of edit operations to perform",
        min_length=1,
    )


class TaskDeletionResult(BaseModel):
    """Result of a task deletion operation."""

    task_id: UUID = Field(description="UUID of the deleted task")
    status: str = Field("deleted", description="Status indicator")
    deletion_confirmed: bool = Field(default=True, description="Confirmation flag")


class EditTasksResponse(BaseModel):
    """Response for edit_tasks tool."""

    edited: list[TaskModel | TaskDeletionResult] = Field(
        description="Edited tasks with updated data or deletion confirmation",
    )


class SearchTasksRequest(BaseModel):
    """Request for search_tasks tool."""

    model_config = ConfigDict(extra="forbid")

    status: str | None = Field(default=None, description="Filter by status")
    search: str | None = Field(default=None, description="Text search in name/details")
    created_after: str | None = Field(
        default=None,
        description="Filter by creation date (ISO format)",
    )
    limit: int = Field(default=50, ge=1, le=200, description="Maximum tasks to return")
    offset: int = Field(default=0, ge=0, description="Result offset for pagination")


class TaskSummary(BaseModel):
    """Compact task summary for search results."""

    task_id: str = Field(description="Task UUID")
    name: str = Field(description="Task name")
    status: str = Field(description="Task status")


class SearchTasksResponse(BaseModel):
    """Response for search_tasks tool."""

    tasks: list[TaskSummary] = Field(description="Matching tasks (compact format)")
    total_count: int = Field(description="Total number of matching tasks")


class GetTasksRequest(BaseModel):
    """Request for get_tasks tool."""

    model_config = ConfigDict(extra="forbid")

    task_ids: list[str] = Field(
        description="List of task UUIDs to retrieve",
        min_length=1,
    )


class GetTasksResponse(BaseModel):
    """Response for get_tasks tool."""

    tasks: list[TaskModel] = Field(
        description="Full task details including relationships",
    )


# ========== Tool Implementations ==========


def project_info(service: TaskService, project_path: Path) -> ProjectInfoResponse:
    """Get project information and metadata.

    Args:
        service: TaskService instance
        project_path: Path to the project

    Returns:
        ProjectInfoResponse with project metadata

    """
    # Get task counts by status
    all_tasks = service.get_all_tasks()
    task_counts = {
        "pending": sum(1 for t in all_tasks if t.status == TaskStatus.PENDING),
        "completed": sum(1 for t in all_tasks if t.status == TaskStatus.COMPLETED),
        "cancelled": sum(1 for t in all_tasks if t.status == TaskStatus.CANCELLED),
    }

    description = _load_project_description(project_path)

    return ProjectInfoResponse(
        project_name=project_path.name,
        project_description=description,
        project_path=str(project_path),
        available_statuses=[s.value for s in TaskStatus],
        task_counts=task_counts,
    )


def create_tasks(
    service: TaskService,
    request: CreateTasksRequest,
) -> CreateTasksResponse:
    """Create one or more tasks.

    Args:
        service: TaskService instance
        request: CreateTasksRequest with task specifications

    Returns:
        CreateTasksResponse with created tasks

    Raises:
        MCPValidationError: If task creation fails

    """
    created_tasks: list[TaskModel] = []
    persisted_task_ids: list[UUID] = []
    current_spec: TaskCreateSpec | None = None

    try:
        for spec in request.tasks:
            current_spec = spec
            task = service.create_task(name=spec.name, details=spec.details or "N/A")
            persisted_task_ids.append(task.task_id)
            created_tasks.append(task)
    except MCPValidationError:
        _rollback_created_tasks(service, persisted_task_ids)
        raise
    except Exception as e:
        _rollback_created_tasks(service, persisted_task_ids)
        name = current_spec.name if current_spec else "unknown"
        msg = f"Failed to create task '{name}': {e}"
        raise MCPValidationError(
            msg,
            suggestions=["Verify task names and details are valid"],
        ) from e

    return CreateTasksResponse(created=created_tasks)


def _handle_update_action(
    service: TaskService,
    task_id: UUID,
    op: EditTaskOperation,
) -> TaskModel:
    """Handle update action on a task.

    Args:
        service: TaskService instance
        task_id: UUID of the task to update
        op: Edit operation with update details

    Returns:
        Updated task

    """
    task = service.get_task(task_id)
    if op.name is not None:
        task.name = op.name
    if op.details is not None:
        task.details = op.details
    service.update_task(task)
    return task


def _handle_delete_action(
    service: TaskService,
    task_id: UUID,
    op: EditTaskOperation,  # noqa: ARG001
) -> TaskDeletionResult:
    """Handle delete action on a task.

    Args:
        service: TaskService instance
        task_id: UUID of the task to delete
        op: Edit operation (unused but kept for signature consistency)

    Returns:
        Deletion confirmation

    """
    service.delete_task(task_id)
    return TaskDeletionResult(
        task_id=task_id,
        status="deleted",
        deletion_confirmed=True,
    )


def _handle_state_transition_action(
    service: TaskService,
    task_id: UUID,
    action: str,
) -> TaskModel:
    """Handle state transition actions (complete, cancel, reopen).

    Args:
        service: TaskService instance
        task_id: UUID of the task to transition
        action: Transition action name

    Returns:
        Updated task

    """
    action_map = {
        "complete": service.complete_task,
        "cancel": service.cancel_task,
        "reopen": service.reopen_task,
    }
    transition = action_map[action]
    transition(task_id)
    return service.get_task(task_id)


def edit_tasks(  # noqa: C901
    service: TaskService,
    request: EditTasksRequest,
) -> EditTasksResponse:
    """Edit one or more tasks.

    Args:
        service: TaskService instance
        request: EditTasksRequest with edit operations

    Returns:
        EditTasksResponse with edited tasks

    Raises:
        MCPValidationError: If edit operation fails

    """

    def _invalid_action(action: str) -> NoReturn:
        valid_actions = {"update", "delete", "complete", "cancel", "reopen"}
        msg = f"Unknown action: {action}"
        raise MCPValidationError(
            msg,
            suggestions=[f"Valid actions: {', '.join(sorted(valid_actions))}"],
        )

    edited_tasks: list[TaskModel | TaskDeletionResult] = []
    rollback_actions: list[Callable[[], None]] = []
    current_op: EditTaskOperation | None = None

    try:
        for op in request.operations:
            current_op = op
            try:
                task_id = UUID(op.task_id)
            except (ValueError, TypeError) as e:
                msg = f"Invalid task_id: {op.task_id}"
                raise MCPValidationError(
                    msg,
                    suggestions=["Provide a valid UUID"],
                ) from e

            # Create rollback snapshot before modification
            task = service.get_task(task_id)
            snapshot = task.model_copy(deep=True)

            def _restore_snapshot(saved_task: TaskModel = snapshot) -> None:
                service.repository.save_task(saved_task)  # type: ignore[attr-defined]

            rollback_actions.append(_restore_snapshot)

            # Execute action using handler dispatch
            if op.action == "update":
                result = _handle_update_action(service, task_id, op)
            elif op.action == "delete":
                result = _handle_delete_action(service, task_id, op)
            elif op.action in {"complete", "cancel", "reopen"}:
                result = _handle_state_transition_action(service, task_id, op.action)
            else:
                _invalid_action(op.action)

            edited_tasks.append(result)

    except MCPValidationError:
        _rollback_edits(rollback_actions)
        raise
    except Exception as e:
        _rollback_edits(rollback_actions)
        task_id_str = current_op.task_id if current_op else "unknown"
        msg = f"Failed to edit task '{task_id_str}': {e}"
        raise MCPValidationError(msg) from e

    return EditTasksResponse(edited=edited_tasks)


def search_tasks(  # noqa: C901
    service: TaskService,
    request: SearchTasksRequest,
) -> SearchTasksResponse:
    """Search for tasks with filters (compact results).

    Args:
        service: TaskService instance
        request: SearchTasksRequest with filter criteria

    Returns:
        SearchTasksResponse with compact task summaries

    Raises:
        MCPValidationError: If search parameters are invalid

    """
    # Get initial task list
    if request.status:
        try:
            status_enum = TaskStatus(request.status)
            tasks = service.get_tasks_by_status(status_enum)
        except ValueError as e:
            msg = f"Invalid status: {request.status}"
            raise MCPValidationError(
                msg,
                suggestions=[f"Valid statuses: {', '.join(s.value for s in TaskStatus)}"],
            ) from e
    else:
        tasks = service.get_all_tasks()

    # Apply text search if specified
    if request.search:
        search_lower = request.search.lower()
        tasks = [
            t for t in tasks if search_lower in t.name.lower() or search_lower in t.details.lower()
        ]

    # Apply created_after filter if specified
    if request.created_after:
        try:
            created_after = datetime.fromisoformat(request.created_after).astimezone()
            tasks = [t for t in tasks if t.created_at >= created_after]
        except (ValueError, TypeError) as e:
            msg = f"Invalid created_after format: {request.created_after}"
            raise MCPValidationError(
                msg,
                suggestions=["Use ISO 8601 timestamps, e.g. 2025-01-01T00:00:00+00:00"],
            ) from e

    # Sort by status and created_at
    tasks_sorted = sorted(
        tasks,
        key=lambda t: (t.status.value, t.created_at),
    )

    # Create compact summaries
    summaries: list[TaskSummary] = [
        TaskSummary(
            task_id=str(t.task_id),
            name=t.name,
            status=t.status.value,
        )
        for t in tasks_sorted
    ]

    offset = request.offset
    limit = request.limit
    paged = summaries[offset : offset + limit]

    return SearchTasksResponse(tasks=paged, total_count=len(summaries))


def get_tasks(service: TaskService, request: GetTasksRequest) -> GetTasksResponse:
    """Get full task details for specified task IDs.

    Args:
        service: TaskService instance
        request: GetTasksRequest with task IDs

    Returns:
        GetTasksResponse with full task details

    Raises:
        MCPValidationError: If task IDs are invalid or tasks not found

    """
    tasks: list[TaskModel] = []

    for task_id_str in request.task_ids:
        try:
            task_id = UUID(task_id_str)
            task = service.get_task(task_id)
            tasks.append(task)
        except (ValueError, TypeError) as e:
            msg = f"Invalid task_id: {task_id_str}"
            raise MCPValidationError(
                msg,
                suggestions=["Provide task IDs as UUID strings"],
            ) from e
        except Exception as e:
            msg = f"Failed to get task '{task_id_str}': {e}"
            raise MCPValidationError(msg) from e

    return GetTasksResponse(tasks=tasks)


def _rollback_created_tasks(service: TaskService, task_ids: list[UUID]) -> None:
    """Rollback created tasks by deleting them (best effort).

    Args:
        service: TaskService instance
        task_ids: List of task UUIDs to delete

    """
    for task_id in reversed(task_ids):
        try:
            service.delete_task(task_id)
        except Exception as e:  # pragma: no cover - best effort cleanup  # noqa: BLE001
            logger.debug("Rollback failed for task %s: %s", task_id, e)
            continue


def _rollback_edits(rollback_actions: list[Callable[[], None]]) -> None:
    """Execute rollback actions in reverse order (best effort).

    Args:
        rollback_actions: List of rollback callables to execute

    """
    for i, action in enumerate(reversed(rollback_actions)):
        try:
            action()
        except Exception as e:  # pragma: no cover - best effort cleanup  # noqa: BLE001
            logger.debug("Rollback action %d failed: %s", len(rollback_actions) - i - 1, e)
            continue


def _load_project_description(project_path: Path) -> str:
    config_file = project_path / ".tasky" / "config.toml"
    if config_file.is_file():
        try:
            data = tomllib.loads(config_file.read_text(encoding="utf-8"))
            project_section = data.get("project")
            if isinstance(project_section, dict):
                description = project_section.get("description")  # type: ignore[reportUnknownMemberType]
                if isinstance(description, str) and description.strip():
                    return description.strip()
        except Exception:  # pragma: no cover - config parsing best effort  # noqa: BLE001
            return f"Tasky project at {project_path}"
    return f"Tasky project at {project_path}"
