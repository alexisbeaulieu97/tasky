"""Simplified tests for MCP tools (working with current TaskModel)."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

import pytest
from tasky_mcp_server.errors import MCPValidationError
from tasky_mcp_server.tools import (
    CreateTasksRequest,
    EditTaskOperation,
    EditTasksRequest,
    GetTasksRequest,
    ProjectInfoResponse,
    SearchTasksRequest,
    TaskCreateSpec,
    create_tasks,
    edit_tasks,
    get_tasks,
    project_info,
    search_tasks,
)
from tasky_tasks.enums import TaskStatus
from tasky_tasks.service import TaskService

# ========== project_info Tests ==========


def test_project_info_basic(task_service: TaskService, tmp_path: Path) -> None:
    """Test project_info returns basic metadata."""
    # Create some tasks to populate counts
    task_service.create_task("Task 1", "Details 1")
    task_service.create_task("Task 2", "Details 2")

    response = project_info(task_service, tmp_path)

    assert isinstance(response, ProjectInfoResponse)
    assert response.project_name == tmp_path.name
    assert response.project_description.startswith("Tasky project")
    assert response.project_path == str(tmp_path)
    assert "pending" in response.available_statuses
    assert "completed" in response.available_statuses
    assert response.task_counts["pending"] == 2
    assert response.task_counts["completed"] == 0


# ========== create_tasks Tests ==========


def test_create_single_task(task_service: TaskService) -> None:
    """Test creating a single task."""
    request = CreateTasksRequest(
        tasks=[
            TaskCreateSpec(
                name="Test Task",
                details="Test Details",
            ),
        ],
    )

    response = create_tasks(task_service, request)

    assert len(response.created) == 1
    task = response.created[0]
    assert task["name"] == "Test Task"
    assert task["details"] == "Test Details"
    assert "task_id" in task
    assert UUID(task["task_id"])  # Valid UUID


def test_create_multiple_tasks(task_service: TaskService) -> None:
    """Test creating multiple tasks in one request."""
    request = CreateTasksRequest(
        tasks=[
            TaskCreateSpec(name="Task 1", details="Details 1"),
            TaskCreateSpec(name="Task 2", details="Details 2"),
            TaskCreateSpec(name="Task 3", details="Details 3"),
        ],
    )

    response = create_tasks(task_service, request)

    assert len(response.created) == 3
    names = [t["name"] for t in response.created]
    assert names == ["Task 1", "Task 2", "Task 3"]


def test_create_tasks_rolls_back_on_failure(task_service: TaskService) -> None:
    """Ensure create_tasks leaves no partial results on failure."""
    request = CreateTasksRequest(
        tasks=[
            TaskCreateSpec(name="Valid", details="ok"),
            TaskCreateSpec(name="", details="bad"),
        ],
    )

    with pytest.raises(MCPValidationError):
        create_tasks(task_service, request)

    assert task_service.get_all_tasks() == []


# ========== edit_tasks Tests ==========


def test_edit_task_update_name(task_service: TaskService) -> None:
    """Test updating task name."""
    task = task_service.create_task("Original Name", "Original Details")
    task_id = str(task.task_id)

    request = EditTasksRequest(
        operations=[
            EditTaskOperation(
                task_id=task_id,
                action="update",
                name="Updated Name",
            ),
        ],
    )

    response = edit_tasks(task_service, request)

    assert len(response.edited) == 1
    assert response.edited[0]["name"] == "Updated Name"
    assert response.edited[0]["details"] == "Original Details"


def test_edit_task_update_details(task_service: TaskService) -> None:
    """Test updating task details."""
    task = task_service.create_task("Task Name", "Original Details")
    task_id = str(task.task_id)

    request = EditTasksRequest(
        operations=[
            EditTaskOperation(
                task_id=task_id,
                action="update",
                details="Updated Details",
            ),
        ],
    )

    response = edit_tasks(task_service, request)

    assert len(response.edited) == 1
    assert response.edited[0]["details"] == "Updated Details"


def test_edit_task_complete(task_service: TaskService) -> None:
    """Test completing a task."""
    task = task_service.create_task("Task to Complete", "Details")
    task_id = str(task.task_id)

    request = EditTasksRequest(
        operations=[
            EditTaskOperation(task_id=task_id, action="complete"),
        ],
    )

    response = edit_tasks(task_service, request)

    assert len(response.edited) == 1
    assert response.edited[0]["status"] == TaskStatus.COMPLETED.value


def test_edit_task_cancel(task_service: TaskService) -> None:
    """Test cancelling a task."""
    task = task_service.create_task("Task to Cancel", "Details")
    task_id = str(task.task_id)

    request = EditTasksRequest(
        operations=[
            EditTaskOperation(task_id=task_id, action="cancel"),
        ],
    )

    response = edit_tasks(task_service, request)

    assert len(response.edited) == 1
    assert response.edited[0]["status"] == TaskStatus.CANCELLED.value


def test_edit_task_delete(task_service: TaskService) -> None:
    """Test deleting a task."""
    task = task_service.create_task("Task to Delete", "Details")
    task_id = str(task.task_id)

    request = EditTasksRequest(
        operations=[
            EditTaskOperation(task_id=task_id, action="delete"),
        ],
    )

    response = edit_tasks(task_service, request)

    assert len(response.edited) == 1
    assert response.edited[0]["status"] == "deleted"
    assert response.edited[0]["deletion_confirmed"] is True

    # Verify task is actually deleted
    all_tasks = task_service.get_all_tasks()
    assert len(all_tasks) == 0


def test_edit_task_invalid_id(task_service: TaskService) -> None:
    """Test editing non-existent task raises error."""
    request = EditTasksRequest(
        operations=[
            EditTaskOperation(
                task_id="invalid-uuid",
                action="update",
                name="New Name",
            ),
        ],
    )

    with pytest.raises(MCPValidationError, match="Invalid task_id"):
        edit_tasks(task_service, request)


def test_edit_tasks_rolls_back_on_failure(task_service: TaskService) -> None:
    """Ensure edit_tasks reverts earlier operations when one fails."""
    task = task_service.create_task("Original", "Details")
    request = EditTasksRequest(
        operations=[
            EditTaskOperation(task_id=str(task.task_id), action="update", name="Changed"),
            EditTaskOperation(task_id=str(task.task_id), action="unknown"),
        ],
    )

    with pytest.raises(MCPValidationError):
        edit_tasks(task_service, request)

    reloaded = task_service.get_task(task.task_id)
    assert reloaded.name == "Original"


def test_edit_multiple_tasks(task_service: TaskService) -> None:
    """Test editing multiple tasks in one request."""
    task1 = task_service.create_task("Task 1", "Details 1")
    task2 = task_service.create_task("Task 2", "Details 2")

    request = EditTasksRequest(
        operations=[
            EditTaskOperation(
                task_id=str(task1.task_id),
                action="update",
                name="Updated Task 1",
            ),
            EditTaskOperation(task_id=str(task2.task_id), action="complete"),
        ],
    )

    response = edit_tasks(task_service, request)

    assert len(response.edited) == 2
    assert response.edited[0]["name"] == "Updated Task 1"
    assert response.edited[1]["status"] == TaskStatus.COMPLETED.value


# ========== search_tasks Tests ==========


def test_search_all_tasks(task_service: TaskService) -> None:
    """Test searching for all tasks."""
    task_service.create_task("Task 1", "Details 1")
    task_service.create_task("Task 2", "Details 2")

    request = SearchTasksRequest()
    response = search_tasks(task_service, request)

    assert response.total_count == 2
    assert len(response.tasks) == 2


def test_search_by_status(task_service: TaskService) -> None:
    """Test filtering by status."""
    _task1 = task_service.create_task("Pending Task", "Details")
    task2 = task_service.create_task("Completed Task", "Details")
    task_service.complete_task(task2.task_id)

    request = SearchTasksRequest(status="completed")
    response = search_tasks(task_service, request)

    assert response.total_count == 1
    assert response.tasks[0].name == "Completed Task"


def test_search_by_text(task_service: TaskService) -> None:
    """Test text search in name and details."""
    task_service.create_task("Important Task", "Regular details")
    task_service.create_task("Regular Task", "Important details")
    task_service.create_task("Other Task", "Other details")

    request = SearchTasksRequest(search="important")
    response = search_tasks(task_service, request)

    assert response.total_count == 2


def test_search_compact_format(task_service: TaskService) -> None:
    """Test search returns compact task summaries."""
    task_service.create_task("Test Task", "Test Details")

    request = SearchTasksRequest()
    response = search_tasks(task_service, request)

    task_summary = response.tasks[0]
    assert task_summary.task_id is not None
    assert task_summary.name == "Test Task"
    assert task_summary.status == TaskStatus.PENDING.value


def test_search_pagination(task_service: TaskService) -> None:
    """Test pagination parameters limit returned tasks."""
    for i in range(5):
        task_service.create_task(f"Task {i}", f"Details {i}")

    request = SearchTasksRequest(limit=2, offset=1)
    response = search_tasks(task_service, request)

    assert response.total_count == 5
    assert len(response.tasks) == 2
    assert response.tasks[0].name == "Task 1"


# ========== get_tasks Tests ==========


def test_get_single_task(task_service: TaskService) -> None:
    """Test getting full details for a single task."""
    task = task_service.create_task("Test Task", "Test Details")
    task_id = str(task.task_id)

    request = GetTasksRequest(task_ids=[task_id])
    response = get_tasks(task_service, request)

    assert len(response.tasks) == 1
    assert response.tasks[0]["task_id"] == task_id
    assert response.tasks[0]["name"] == "Test Task"
    assert response.tasks[0]["details"] == "Test Details"
    assert "created_at" in response.tasks[0]
    assert "updated_at" in response.tasks[0]


def test_get_multiple_tasks(task_service: TaskService) -> None:
    """Test getting multiple tasks by ID."""
    task1 = task_service.create_task("Task 1", "Details 1")
    task2 = task_service.create_task("Task 2", "Details 2")
    task_ids = [str(task1.task_id), str(task2.task_id)]

    request = GetTasksRequest(task_ids=task_ids)
    response = get_tasks(task_service, request)

    assert len(response.tasks) == 2
    names = [t["name"] for t in response.tasks]
    assert set(names) == {"Task 1", "Task 2"}


def test_get_task_invalid_id(task_service: TaskService) -> None:
    """Test getting task with invalid ID raises error."""
    request = GetTasksRequest(task_ids=["not-a-uuid"])

    with pytest.raises(MCPValidationError, match="Invalid task_id"):
        get_tasks(task_service, request)


# ========== Integration Tests ==========


def test_workflow_create_edit_search(task_service: TaskService) -> None:
    """Test full workflow: create -> edit -> search."""
    # Create
    create_req = CreateTasksRequest(
        tasks=[TaskCreateSpec(name="Workflow Task", details="Initial details")],
    )
    create_resp = create_tasks(task_service, create_req)
    task_id = create_resp.created[0]["task_id"]

    # Edit
    edit_req = EditTasksRequest(
        operations=[
            EditTaskOperation(
                task_id=task_id,
                action="update",
                details="Updated details",
            ),
        ],
    )
    edit_tasks(task_service, edit_req)

    # Search
    search_req = SearchTasksRequest(search="workflow")
    search_resp = search_tasks(task_service, search_req)

    assert search_resp.total_count == 1
    assert search_resp.tasks[0].name == "Workflow Task"
