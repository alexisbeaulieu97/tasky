"""Integration tests for MCP server tool workflows."""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from tasky_mcp_server.errors import MCPValidationError
from tasky_mcp_server.tools import (
    CreateTasksRequest,
    EditTaskOperation,
    EditTasksRequest,
    GetTasksRequest,
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


class TestWorkflowIntegration:
    """Test complete workflows combining multiple tools."""

    def test_search_get_edit_workflow(self, task_service: TaskService) -> None:
        """Test complete workflow: search → get_tasks → edit_tasks."""
        # Setup: Create some tasks
        create_req = CreateTasksRequest(
            tasks=[
                TaskCreateSpec(name="Bug: Fix login", details="Auth issue"),
                TaskCreateSpec(name="Feature: Add dashboard", details="New UI"),
                TaskCreateSpec(name="Bug: Fix logout", details="Session issue"),
            ],
        )
        create_tasks(task_service, create_req)

        # Step 1: Search for bugs
        search_req = SearchTasksRequest(search="bug")
        search_resp = search_tasks(task_service, search_req)
        assert search_resp.total_count == 2
        bug_ids = [t.task_id for t in search_resp.tasks]

        # Step 2: Get full details
        get_req = GetTasksRequest(task_ids=bug_ids)
        get_resp = get_tasks(task_service, get_req)
        assert len(get_resp.tasks) == 2
        for task in get_resp.tasks:
            assert "created_at" in task
            assert "updated_at" in task

        # Step 3: Complete both bugs
        edit_req = EditTasksRequest(
            operations=[
                EditTaskOperation(task_id=bug_ids[0], action="complete"),
                EditTaskOperation(task_id=bug_ids[1], action="complete"),
            ],
        )
        edit_resp = edit_tasks(task_service, edit_req)
        assert len(edit_resp.edited) == 2
        for task in edit_resp.edited:
            assert task["status"] == TaskStatus.COMPLETED.value

    def test_project_info_then_create_workflow(
        self,
        task_service: TaskService,
        tmp_path: Path,
    ) -> None:
        """Test workflow: project_info → create_tasks."""
        # Step 1: Get project info
        info_resp = project_info(task_service, tmp_path)
        assert "pending" in info_resp.available_statuses
        assert info_resp.task_counts["pending"] == 0

        # Step 2: Create tasks based on available options
        create_req = CreateTasksRequest(
            tasks=[
                TaskCreateSpec(name="Task 1", details="Details 1"),
                TaskCreateSpec(name="Task 2", details="Details 2"),
            ],
        )
        create_resp = create_tasks(task_service, create_req)
        assert len(create_resp.created) == 2

        # Step 3: Verify project info updated
        info_resp2 = project_info(task_service, tmp_path)
        assert info_resp2.task_counts["pending"] == 2

    def test_bulk_create_update_delete_workflow(
        self,
        task_service: TaskService,
    ) -> None:
        """Test bulk operations: create 5 → update 3 → delete 1."""
        # Step 1: Create 5 tasks
        create_req = CreateTasksRequest(
            tasks=[TaskCreateSpec(name=f"Task {i}", details=f"Details {i}") for i in range(1, 6)],
        )
        create_resp = create_tasks(task_service, create_req)
        assert len(create_resp.created) == 5
        task_ids = [t["task_id"] for t in create_resp.created]

        # Step 2: Update 3 tasks
        edit_req = EditTasksRequest(
            operations=[
                EditTaskOperation(
                    task_id=task_ids[0],
                    action="update",
                    name="Updated Task 1",
                ),
                EditTaskOperation(task_id=task_ids[1], action="complete"),
                EditTaskOperation(
                    task_id=task_ids[2],
                    action="update",
                    details="Updated Details 3",
                ),
            ],
        )
        edit_resp = edit_tasks(task_service, edit_req)
        assert len(edit_resp.edited) == 3

        # Step 3: Delete 1 task
        delete_req = EditTasksRequest(
            operations=[
                EditTaskOperation(task_id=task_ids[3], action="delete"),
            ],
        )
        delete_resp = edit_tasks(task_service, delete_req)
        assert delete_resp.edited[0]["deletion_confirmed"] is True

        # Verify final state
        all_tasks = task_service.get_all_tasks()
        assert len(all_tasks) == 4  # 5 created - 1 deleted


class TestSearchReturnFormats:
    """Test search returns compact format vs get_tasks full format."""

    def test_search_returns_compact_format(
        self,
        task_service: TaskService,
    ) -> None:
        """Test search_tasks returns compact summaries."""
        task_service.create_task("Test Task", "Test Details")

        search_req = SearchTasksRequest()
        search_resp = search_tasks(task_service, search_req)

        assert search_resp.total_count == 1
        task_summary = search_resp.tasks[0]

        # Compact format has only essential fields
        assert hasattr(task_summary, "task_id")
        assert hasattr(task_summary, "name")
        assert hasattr(task_summary, "status")
        # Should NOT have created_at, updated_at, details in summary

    def test_get_tasks_returns_full_context(
        self,
        task_service: TaskService,
    ) -> None:
        """Test get_tasks returns full task details."""
        task = task_service.create_task("Test Task", "Test Details")

        get_req = GetTasksRequest(task_ids=[str(task.task_id)])
        get_resp = get_tasks(task_service, get_req)

        assert len(get_resp.tasks) == 1
        full_task = get_resp.tasks[0]

        # Full format has all fields
        assert "task_id" in full_task
        assert "name" in full_task
        assert "details" in full_task
        assert "status" in full_task
        assert "created_at" in full_task
        assert "updated_at" in full_task


class TestErrorHandling:
    """Test error scenarios across tools."""

    def test_invalid_task_id_in_get_tasks(
        self,
        task_service: TaskService,
    ) -> None:
        """Test get_tasks with invalid UUID."""
        get_req = GetTasksRequest(task_ids=["not-a-uuid"])

        with pytest.raises(MCPValidationError, match="Invalid task_id"):
            get_tasks(task_service, get_req)

    def test_invalid_status_in_search(
        self,
        task_service: TaskService,
    ) -> None:
        """Test search_tasks with invalid status."""
        search_req = SearchTasksRequest(status="invalid_status")

        with pytest.raises(MCPValidationError, match="Invalid status"):
            search_tasks(task_service, search_req)

    def test_edit_nonexistent_task(
        self,
        task_service: TaskService,
    ) -> None:
        """Test editing a task that doesn't exist."""
        fake_id = str(uuid.uuid4())
        edit_req = EditTasksRequest(
            operations=[
                EditTaskOperation(
                    task_id=fake_id,
                    action="update",
                    name="New Name",
                ),
            ],
        )

        with pytest.raises(MCPValidationError):
            edit_tasks(task_service, edit_req)

    def test_invalid_action_in_edit(
        self,
        task_service: TaskService,
    ) -> None:
        """Test edit_tasks with invalid action."""
        task = task_service.create_task("Test", "Details")

        edit_req = EditTasksRequest(
            operations=[
                EditTaskOperation(
                    task_id=str(task.task_id),
                    action="invalid_action",
                ),
            ],
        )

        with pytest.raises(MCPValidationError, match="Unknown action"):
            edit_tasks(task_service, edit_req)


class TestFilteringBehavior:
    """Test filtering behavior across different scenarios."""

    def test_search_by_status_filter(
        self,
        task_service: TaskService,
    ) -> None:
        """Test status filtering in search."""
        _task1 = task_service.create_task("Pending Task", "Details")
        task2 = task_service.create_task("Completed Task", "Details")
        task_service.complete_task(task2.task_id)

        # Search for completed only
        search_req = SearchTasksRequest(status="completed")
        search_resp = search_tasks(task_service, search_req)

        assert search_resp.total_count == 1
        assert search_resp.tasks[0].task_id == str(task2.task_id)

    def test_search_by_text_filter(
        self,
        task_service: TaskService,
    ) -> None:
        """Test text search filtering."""
        task_service.create_task("Important Meeting", "Discuss Q4 goals")
        task_service.create_task("Code Review", "Review PR #123")
        task_service.create_task("Important Decision", "Choose tech stack")

        # Search for "important"
        search_req = SearchTasksRequest(search="important")
        search_resp = search_tasks(task_service, search_req)

        assert search_resp.total_count == 2
        names = [t.name for t in search_resp.tasks]
        assert "Important Meeting" in names
        assert "Important Decision" in names

    def test_search_combined_filters(
        self,
        task_service: TaskService,
    ) -> None:
        """Test combining multiple filters."""
        task1 = task_service.create_task("Bug: Auth issue", "Login broken")
        task2 = task_service.create_task("Bug: UI glitch", "Button misaligned")
        task_service.complete_task(task1.task_id)

        # Search for pending bugs
        search_req = SearchTasksRequest(status="pending", search="bug")
        search_resp = search_tasks(task_service, search_req)

        assert search_resp.total_count == 1
        assert search_resp.tasks[0].task_id == str(task2.task_id)
