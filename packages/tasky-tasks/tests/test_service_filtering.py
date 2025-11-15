"""Unit tests for task filtering functionality."""

from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest
from tasky_tasks.exceptions import TaskValidationError
from tasky_tasks.models import TaskFilter, TaskModel, TaskStatus
from tasky_tasks.service import TaskService

# Import StorageDataError for testing error handling
try:
    from tasky_storage.errors import StorageDataError
except ModuleNotFoundError:
    StorageDataError = type("StorageDataError", (Exception,), {})  # type: ignore[misc,assignment]


class MockTaskRepository:
    """Mock repository for testing filtering logic."""

    def __init__(self, tasks: list[TaskModel] | None = None) -> None:
        self.tasks = tasks or []

    def initialize(self) -> None:
        """Mock implementation of initialize."""

    def save_task(self, task: TaskModel) -> None:
        """Mock implementation of save_task."""

    def get_task(self, task_id: UUID) -> TaskModel | None:
        """Mock implementation of get_task."""
        for task in self.tasks:
            if task.task_id == task_id:
                return task
        return None

    def get_all_tasks(self) -> list[TaskModel]:
        """Mock implementation of get_all_tasks."""
        return self.tasks

    def delete_task(self, task_id: UUID) -> bool:  # noqa: ARG002
        """Mock implementation of delete_task."""
        return False

    def task_exists(self, task_id: UUID) -> bool:
        """Mock implementation of task_exists."""
        return any(task.task_id == task_id for task in self.tasks)

    def get_tasks_by_status(self, status: TaskStatus) -> list[TaskModel]:
        """Mock implementation of get_tasks_by_status."""
        return [task for task in self.tasks if task.status == status]

    def find_tasks(self, task_filter: TaskFilter) -> list[TaskModel]:
        """Mock implementation of find_tasks."""
        return [task for task in self.tasks if task_filter.matches(task)]


class TestTaskFiltering:
    """Test suite for task filtering functionality."""

    @pytest.fixture
    def sample_tasks(self) -> list[TaskModel]:
        """Create a diverse set of sample tasks for testing."""
        return [
            TaskModel(
                task_id=uuid4(),
                name="Pending Task 1",
                details="Details",
                status=TaskStatus.PENDING,
            ),
            TaskModel(
                task_id=uuid4(),
                name="Pending Task 2",
                details="Details",
                status=TaskStatus.PENDING,
            ),
            TaskModel(
                task_id=uuid4(),
                name="Completed Task 1",
                details="Details",
                status=TaskStatus.COMPLETED,
            ),
            TaskModel(
                task_id=uuid4(),
                name="Completed Task 2",
                details="Details",
                status=TaskStatus.COMPLETED,
            ),
            TaskModel(
                task_id=uuid4(),
                name="Cancelled Task 1",
                details="Details",
                status=TaskStatus.CANCELLED,
            ),
        ]

    @pytest.fixture
    def service_with_tasks(self, sample_tasks: list[TaskModel]) -> TaskService:
        """Create a service with sample tasks."""
        repository = MockTaskRepository(tasks=sample_tasks)
        return TaskService(repository=repository)

    @pytest.fixture
    def empty_service(self) -> TaskService:
        """Create a service with no tasks."""
        repository = MockTaskRepository()
        return TaskService(repository=repository)

    def test_get_tasks_by_status_pending(self, service_with_tasks: TaskService) -> None:
        """Test filtering for pending tasks."""
        tasks = service_with_tasks.get_tasks_by_status(TaskStatus.PENDING)
        assert len(tasks) == 2
        assert all(task.status == TaskStatus.PENDING for task in tasks)

    def test_get_tasks_by_status_completed(self, service_with_tasks: TaskService) -> None:
        """Test filtering for completed tasks."""
        tasks = service_with_tasks.get_tasks_by_status(TaskStatus.COMPLETED)
        assert len(tasks) == 2
        assert all(task.status == TaskStatus.COMPLETED for task in tasks)

    def test_get_tasks_by_status_cancelled(self, service_with_tasks: TaskService) -> None:
        """Test filtering for cancelled tasks."""
        tasks = service_with_tasks.get_tasks_by_status(TaskStatus.CANCELLED)
        assert len(tasks) == 1
        assert all(task.status == TaskStatus.CANCELLED for task in tasks)

    def test_get_pending_tasks(self, service_with_tasks: TaskService) -> None:
        """Test convenience method for pending tasks."""
        tasks = service_with_tasks.get_pending_tasks()
        assert len(tasks) == 2
        assert all(task.status == TaskStatus.PENDING for task in tasks)

    def test_get_completed_tasks(self, service_with_tasks: TaskService) -> None:
        """Test convenience method for completed tasks."""
        tasks = service_with_tasks.get_completed_tasks()
        assert len(tasks) == 2
        assert all(task.status == TaskStatus.COMPLETED for task in tasks)

    def test_get_cancelled_tasks(self, service_with_tasks: TaskService) -> None:
        """Test convenience method for cancelled tasks."""
        tasks = service_with_tasks.get_cancelled_tasks()
        assert len(tasks) == 1
        assert all(task.status == TaskStatus.CANCELLED for task in tasks)

    def test_filtering_empty_repository(self, empty_service: TaskService) -> None:
        """Test filtering returns empty list when no tasks exist."""
        assert empty_service.get_pending_tasks() == []
        assert empty_service.get_completed_tasks() == []
        assert empty_service.get_cancelled_tasks() == []

    def test_filtering_returns_only_matching_status(self, service_with_tasks: TaskService) -> None:
        """Test that filtering returns only tasks with matching status."""
        pending_tasks = service_with_tasks.get_pending_tasks()
        completed_tasks = service_with_tasks.get_completed_tasks()
        cancelled_tasks = service_with_tasks.get_cancelled_tasks()

        # Verify no overlap between filtered results
        pending_ids = {task.task_id for task in pending_tasks}
        completed_ids = {task.task_id for task in completed_tasks}
        cancelled_ids = {task.task_id for task in cancelled_tasks}

        assert not pending_ids.intersection(completed_ids)
        assert not pending_ids.intersection(cancelled_ids)
        assert not completed_ids.intersection(cancelled_ids)

    def test_get_tasks_by_status_converts_storage_error_to_domain_error(self) -> None:
        """Test that StorageDataError from repository is converted to TaskValidationError."""
        repository = MockTaskRepository()
        # Mock the repository to throw StorageDataError
        repository.get_tasks_by_status = Mock(side_effect=StorageDataError("Corrupted data"))
        service = TaskService(repository=repository)

        with pytest.raises(TaskValidationError) as exc_info:
            service.get_tasks_by_status(TaskStatus.PENDING)

        # Verify the error message mentions corrupted data
        assert "corrupted" in str(exc_info.value).lower()
        # Verify the cause is StorageDataError
        assert isinstance(exc_info.value.__cause__, StorageDataError)
