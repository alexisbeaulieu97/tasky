"""MCP tools for task management.

This module implements the 5 core MCP tools:
1. project_info - Get project metadata and status options
2. create_tasks - Bulk create tasks
3. edit_tasks - Bulk edit/update/delete tasks
4. search_tasks - Find tasks with filters (compact format)
5. get_tasks - Retrieve full task details by ID
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import UUID

from pydantic import BaseModel, Field
from tasky_tasks.enums import TaskStatus

from tasky_mcp_server.errors import MCPValidationError

if TYPE_CHECKING:
    from tasky_tasks.service import TaskService


# ========== Tool Request/Response Models ==========


class ProjectInfoResponse(BaseModel):
    """Response for project_info tool."""

    project_name: str = Field(description="Name of the project")
    project_path: str = Field(description="Path to the project")
    available_statuses: list[str] = Field(
        description="Valid task status values",
    )
    task_counts: dict[str, int] = Field(
        description="Count of tasks by status",
    )


class TaskCreateSpec(BaseModel):
    """Specification for creating a task."""

    name: str = Field(..., description="Task name")
    details: str | None = Field(None, description="Task details")


class CreateTasksRequest(BaseModel):
    """Request for create_tasks tool."""

    tasks: list[TaskCreateSpec] = Field(
        description="List of tasks to create",
        min_length=1,
    )


class CreateTasksResponse(BaseModel):
    """Response for create_tasks tool."""

    created: list[dict[str, Any]] = Field(
        description="Created tasks with IDs and timestamps",
    )


class EditTaskOperation(BaseModel):
    """Single edit operation for a task."""

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

    operations: list[EditTaskOperation] = Field(
        description="List of edit operations to perform",
        min_length=1,
    )


class EditTasksResponse(BaseModel):
    """Response for edit_tasks tool."""

    edited: list[dict[str, Any]] = Field(
        description="Edited tasks with updated data",
    )


class SearchTasksRequest(BaseModel):
    """Request for search_tasks tool."""

    status: str | None = Field(default=None, description="Filter by status")
    search: str | None = Field(default=None, description="Text search in name/details")
    created_after: str | None = Field(
        default=None,
        description="Filter by creation date (ISO format)",
    )


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

    task_ids: list[str] = Field(
        description="List of task UUIDs to retrieve",
        min_length=1,
    )


class GetTasksResponse(BaseModel):
    """Response for get_tasks tool."""

    tasks: list[dict[str, Any]] = Field(
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

    return ProjectInfoResponse(
        project_name=project_path.name,
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
    created_tasks = []

    for spec in request.tasks:
        try:
            # Create the task
            task = service.create_task(name=spec.name, details=spec.details or "N/A")

            created_tasks.append(task.model_dump(mode="json"))

        except MCPValidationError:
            raise
        except Exception as e:
            msg = f"Failed to create task '{spec.name}': {e}"
            raise MCPValidationError(msg) from e

    return CreateTasksResponse(created=created_tasks)


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

    def _validate_action(action: str) -> None:
        """Validate that the action is supported.

        Args:
            action: The action to validate

        Raises:
            MCPValidationError: If action is not supported

        """
        valid_actions = {"update", "delete", "complete", "cancel", "reopen"}
        if action not in valid_actions:
            msg = f"Unknown action: {action}"
            raise MCPValidationError(msg)

    edited_tasks = []

    for op in request.operations:
        try:
            # Parse task ID
            try:
                task_id = UUID(op.task_id)
            except (ValueError, TypeError) as e:
                msg = f"Invalid task_id: {op.task_id}"
                raise MCPValidationError(msg) from e

            # Get the task
            task = service.get_task(task_id)

            # Perform the action
            if op.action == "update":
                if op.name is not None:
                    task.name = op.name
                if op.details is not None:
                    task.details = op.details
                service.update_task(task)

            elif op.action == "delete":
                service.delete_task(task_id)
                # Return a minimal response for deleted tasks
                edited_tasks.append(
                    {
                        "task_id": str(task_id),
                        "status": "deleted",
                        "deletion_confirmed": True,
                    },
                )
                continue

            elif op.action == "complete":
                service.complete_task(task_id)
                task = service.get_task(task_id)

            elif op.action == "cancel":
                service.cancel_task(task_id)
                task = service.get_task(task_id)

            elif op.action == "reopen":
                service.reopen_task(task_id)
                task = service.get_task(task_id)

            else:
                _validate_action(op.action)

            edited_tasks.append(task.model_dump(mode="json"))

        except MCPValidationError:
            raise
        except Exception as e:
            msg = f"Failed to edit task '{op.task_id}': {e}"
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
            raise MCPValidationError(msg) from e
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
            raise MCPValidationError(msg) from e

    # Sort by status and created_at
    tasks_sorted = sorted(
        tasks,
        key=lambda t: (t.status.value, t.created_at),
    )

    # Create compact summaries
    summaries = [
        TaskSummary(
            task_id=str(t.task_id),
            name=t.name,
            status=t.status.value,
        )
        for t in tasks_sorted
    ]

    return SearchTasksResponse(tasks=summaries, total_count=len(summaries))


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
    tasks = []

    for task_id_str in request.task_ids:
        try:
            task_id = UUID(task_id_str)
            task = service.get_task(task_id)
            tasks.append(task.model_dump(mode="json"))
        except (ValueError, TypeError) as e:
            msg = f"Invalid task_id: {task_id_str}"
            raise MCPValidationError(msg) from e
        except Exception as e:
            msg = f"Failed to get task '{task_id_str}': {e}"
            raise MCPValidationError(msg) from e

    return GetTasksResponse(tasks=tasks)
