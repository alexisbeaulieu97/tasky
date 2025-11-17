"""Integration tests for backend migration scenarios."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest
from tasky_storage.backends.json import JsonTaskRepository
from tasky_storage.backends.sqlite import SqliteTaskRepository
from tasky_tasks.models import TaskFilter, TaskModel, TaskStatus


class TestBackendMigration:
    """Test data migration between storage backends."""

    def test_json_to_sqlite_migration_preserves_all_fields(self, tmp_path: Path) -> None:
        """Test that migrating from JSON to SQLite preserves all task fields."""
        json_path = tmp_path / "tasks.json"
        sqlite_path = tmp_path / "tasks.db"

        # Create JSON repository with tasks
        json_repo = JsonTaskRepository.from_path(json_path)

        # Create diverse set of tasks
        task1 = TaskModel(name="Pending Task", details="Test pending")
        task2 = TaskModel(name="Completed Task", details="Test completed")
        task2.complete()
        task3 = TaskModel(name="Cancelled Task", details="Test cancelled")
        task3.cancel()

        json_repo.save_task(task1)
        json_repo.save_task(task2)
        json_repo.save_task(task3)

        # Migrate to SQLite
        sqlite_repo = SqliteTaskRepository.from_path(sqlite_path)
        for task in json_repo.get_all_tasks():
            sqlite_repo.save_task(task)

        # Verify all fields preserved
        migrated_tasks = sqlite_repo.get_all_tasks()
        assert len(migrated_tasks) == 3

        # Find each task and verify fields
        migrated_task1 = sqlite_repo.get_task(task1.task_id)
        assert migrated_task1 is not None
        assert migrated_task1.name == task1.name
        assert migrated_task1.details == task1.details
        assert migrated_task1.status == task1.status
        assert migrated_task1.created_at == task1.created_at
        assert migrated_task1.updated_at == task1.updated_at

        migrated_task2 = sqlite_repo.get_task(task2.task_id)
        assert migrated_task2 is not None
        assert migrated_task2.status == TaskStatus.COMPLETED

        migrated_task3 = sqlite_repo.get_task(task3.task_id)
        assert migrated_task3 is not None
        assert migrated_task3.status == TaskStatus.CANCELLED

    def test_sqlite_to_json_migration_preserves_all_fields(self, tmp_path: Path) -> None:
        """Test that migrating from SQLite to JSON preserves all task fields."""
        sqlite_path = tmp_path / "tasks.db"
        json_path = tmp_path / "tasks.json"

        # Create SQLite repository with tasks
        sqlite_repo = SqliteTaskRepository.from_path(sqlite_path)

        task1 = TaskModel(name="SQLite Task 1", details="Test 1")
        task2 = TaskModel(name="SQLite Task 2", details="Test 2")
        task2.complete()

        sqlite_repo.save_task(task1)
        sqlite_repo.save_task(task2)

        # Migrate to JSON
        json_repo = JsonTaskRepository.from_path(json_path)
        for task in sqlite_repo.get_all_tasks():
            json_repo.save_task(task)

        # Verify all fields preserved
        migrated_tasks = json_repo.get_all_tasks()
        assert len(migrated_tasks) == 2

        migrated_task1 = json_repo.get_task(task1.task_id)
        assert migrated_task1 is not None
        assert migrated_task1.name == task1.name
        assert migrated_task1.details == task1.details
        assert migrated_task1.status == task1.status
        assert migrated_task1.created_at == task1.created_at
        assert migrated_task1.updated_at == task1.updated_at

    def test_large_dataset_migration_stress_test(self, tmp_path: Path) -> None:
        """Test migrating 1000+ tasks between backends."""
        json_path = tmp_path / "tasks.json"
        sqlite_path = tmp_path / "tasks.db"

        # Create 1000 tasks in JSON
        json_repo = JsonTaskRepository.from_path(json_path)

        tasks_to_migrate: list[TaskModel] = []
        for i in range(1000):
            task = TaskModel(name=f"Task-{i:04d}", details=f"Details {i}")
            if i % 3 == 0:
                task.complete()
            elif i % 5 == 0:
                task.cancel()
            json_repo.save_task(task)
            tasks_to_migrate.append(task)

        # Migrate to SQLite
        sqlite_repo = SqliteTaskRepository.from_path(sqlite_path)
        for task in json_repo.get_all_tasks():
            sqlite_repo.save_task(task)

        # Verify count
        migrated_tasks = sqlite_repo.get_all_tasks()
        assert len(migrated_tasks) == 1000

        # Verify status distribution matches
        json_pending = len(json_repo.get_tasks_by_status(TaskStatus.PENDING))
        json_completed = len(json_repo.get_tasks_by_status(TaskStatus.COMPLETED))
        json_cancelled = len(json_repo.get_tasks_by_status(TaskStatus.CANCELLED))

        sqlite_pending = len(sqlite_repo.get_tasks_by_status(TaskStatus.PENDING))
        sqlite_completed = len(sqlite_repo.get_tasks_by_status(TaskStatus.COMPLETED))
        sqlite_cancelled = len(sqlite_repo.get_tasks_by_status(TaskStatus.CANCELLED))

        assert json_pending == sqlite_pending
        assert json_completed == sqlite_completed
        assert json_cancelled == sqlite_cancelled

    def test_migration_partial_state_after_error(self, tmp_path: Path) -> None:
        """Test that migration errors leave detectable partial state."""
        json_path = tmp_path / "tasks.json"
        sqlite_path = tmp_path / "tasks.db"

        # Create JSON repository with tasks
        json_repo = JsonTaskRepository.from_path(json_path)
        for i in range(10):
            task = TaskModel(name=f"Task-{i}", details=f"Details {i}")
            json_repo.save_task(task)

        # Create SQLite repository
        sqlite_repo = SqliteTaskRepository.from_path(sqlite_path)

        # Simulate partial migration with error
        def _migrate_with_simulated_error() -> int:
            """Simulate migration error after 5 tasks."""
            count = 0
            for i, task in enumerate(json_repo.get_all_tasks()):
                if i == 5:
                    # Simulate error during migration
                    msg = "Simulated migration error"
                    raise ValueError(msg)
                sqlite_repo.save_task(task)
                count += 1
            return count

        migration_error_occurred = False
        migrated_count = 0
        try:
            migrated_count = _migrate_with_simulated_error()
        except ValueError:
            migration_error_occurred = True

        # Verify error occurred and partial migration happened
        assert migration_error_occurred
        assert migrated_count == 0  # Count not updated before exception
        assert len(sqlite_repo.get_all_tasks()) == 5

        # Verify we can detect partial state for recovery/cleanup

    def test_filtering_behavior_identical_after_migration(self, tmp_path: Path) -> None:
        """Test that filtering produces identical results after migration."""
        json_path = tmp_path / "tasks.json"
        sqlite_path = tmp_path / "tasks.db"

        # Create JSON repository with diverse tasks
        json_repo = JsonTaskRepository.from_path(json_path)

        # Create tasks with specific patterns for filtering
        for i in range(100):
            task = TaskModel(name=f"Task-{i:03d}", details=f"Details {i}")
            if i % 2 == 0:
                task.complete()
            json_repo.save_task(task)

        # Create filter
        task_filter = TaskFilter(statuses=[TaskStatus.COMPLETED])

        # Get results from JSON
        json_results = json_repo.find_tasks(task_filter)
        json_ids = {task.task_id for task in json_results}

        # Migrate to SQLite
        sqlite_repo = SqliteTaskRepository.from_path(sqlite_path)
        for task in json_repo.get_all_tasks():
            sqlite_repo.save_task(task)

        # Get results from SQLite with same filter
        sqlite_results = sqlite_repo.find_tasks(task_filter)
        sqlite_ids = {task.task_id for task in sqlite_results}

        # Verify identical results
        assert len(json_results) == len(sqlite_results)
        assert json_ids == sqlite_ids

    def test_timestamps_preserved_across_migration(self, tmp_path: Path) -> None:
        """Test that created_at and updated_at timestamps are preserved."""
        json_path = tmp_path / "tasks.json"
        sqlite_path = tmp_path / "tasks.db"

        # Create JSON repository
        json_repo = JsonTaskRepository.from_path(json_path)

        # Create task with specific timestamp
        task = TaskModel(name="Timestamp Test", details="Testing timestamps")
        original_created = task.created_at

        json_repo.save_task(task)

        # Update the task
        task.name = "Updated Name"
        task.mark_updated()
        json_repo.save_task(task)
        updated_timestamp = task.updated_at

        # Migrate to SQLite
        sqlite_repo = SqliteTaskRepository.from_path(sqlite_path)
        source_task = json_repo.get_task(task.task_id)
        assert source_task is not None
        sqlite_repo.save_task(source_task)

        # Verify timestamps preserved
        migrated_task = sqlite_repo.get_task(task.task_id)
        assert migrated_task is not None
        assert migrated_task.created_at == original_created
        assert migrated_task.updated_at == updated_timestamp
        assert migrated_task.updated_at > migrated_task.created_at

    def test_migration_with_empty_database(self, tmp_path: Path) -> None:
        """Test migrating from empty database."""
        json_path = tmp_path / "tasks.json"
        sqlite_path = tmp_path / "tasks.db"

        # Create empty JSON repository
        json_repo = JsonTaskRepository.from_path(json_path)
        assert len(json_repo.get_all_tasks()) == 0

        # Migrate to SQLite
        sqlite_repo = SqliteTaskRepository.from_path(sqlite_path)
        for task in json_repo.get_all_tasks():
            sqlite_repo.save_task(task)

        # Verify empty after migration
        assert len(sqlite_repo.get_all_tasks()) == 0


class TestCrossBackendBehavioralIdentity:
    """Test that both backends behave identically for all operations."""

    @pytest.fixture
    def json_repo(self, tmp_path: Path) -> JsonTaskRepository:
        """Create a JSON repository."""
        return JsonTaskRepository.from_path(tmp_path / "tasks.json")

    @pytest.fixture
    def sqlite_repo(self, tmp_path: Path) -> SqliteTaskRepository:
        """Create a SQLite repository."""
        return SqliteTaskRepository.from_path(tmp_path / "tasks.db")

    def test_identical_save_and_retrieve(
        self,
        json_repo: JsonTaskRepository,
        sqlite_repo: SqliteTaskRepository,
    ) -> None:
        """Test that save and retrieve work identically."""
        task1 = TaskModel(name="Test", details="Test details")

        # Save to both
        json_repo.save_task(task1)
        sqlite_repo.save_task(task1)

        # Retrieve from both
        json_task = json_repo.get_task(task1.task_id)
        sqlite_task = sqlite_repo.get_task(task1.task_id)

        # Verify identical
        assert json_task is not None
        assert sqlite_task is not None
        assert json_task.task_id == sqlite_task.task_id
        assert json_task.name == sqlite_task.name
        assert json_task.details == sqlite_task.details
        assert json_task.status == sqlite_task.status

    def test_identical_filtering_results(
        self,
        json_repo: JsonTaskRepository,
        sqlite_repo: SqliteTaskRepository,
    ) -> None:
        """Test that filtering produces identical results."""
        # Create identical dataset in both using same task instances
        tasks: list[TaskModel] = []
        for i in range(50):
            task = TaskModel(name=f"Task-{i}", details=f"Details {i}")
            if i % 3 == 0:
                task.complete()
            tasks.append(task)
            json_repo.save_task(task)
            sqlite_repo.save_task(task)

        # Filter both
        json_completed = json_repo.get_tasks_by_status(TaskStatus.COMPLETED)
        sqlite_completed = sqlite_repo.get_tasks_by_status(TaskStatus.COMPLETED)

        # Verify counts and IDs match
        assert len(json_completed) == len(sqlite_completed)
        json_ids = {t.task_id for t in json_completed}
        sqlite_ids = {t.task_id for t in sqlite_completed}
        assert json_ids == sqlite_ids

    def test_edge_case_empty_database(
        self,
        json_repo: JsonTaskRepository,
        sqlite_repo: SqliteTaskRepository,
    ) -> None:
        """Test both backends handle empty database identically."""
        # Both should return empty lists
        assert len(json_repo.get_all_tasks()) == 0
        assert len(sqlite_repo.get_all_tasks()) == 0

        # Both should return None for nonexistent task
        fake_id = uuid4()
        assert json_repo.get_task(fake_id) is None
        assert sqlite_repo.get_task(fake_id) is None

    def test_edge_case_single_task(
        self,
        json_repo: JsonTaskRepository,
        sqlite_repo: SqliteTaskRepository,
    ) -> None:
        """Test both backends handle single task identically."""
        task = TaskModel(name="Single", details="Only one")

        json_repo.save_task(task)
        sqlite_repo.save_task(task)

        # Both should return list with one task
        json_tasks = json_repo.get_all_tasks()
        sqlite_tasks = sqlite_repo.get_all_tasks()

        assert len(json_tasks) == 1
        assert len(sqlite_tasks) == 1
        assert json_tasks[0].task_id == sqlite_tasks[0].task_id

    def test_edge_case_max_length_strings(
        self,
        json_repo: JsonTaskRepository,
        sqlite_repo: SqliteTaskRepository,
    ) -> None:
        """Test both backends handle very long strings identically."""
        # Create task with very long name and details
        long_name = "A" * 1000
        long_details = "B" * 10000

        task = TaskModel(name=long_name, details=long_details)

        json_repo.save_task(task)
        sqlite_repo.save_task(task)

        # Retrieve from both
        json_task = json_repo.get_task(task.task_id)
        sqlite_task = sqlite_repo.get_task(task.task_id)

        # Verify both preserved the full strings
        assert json_task is not None
        assert sqlite_task is not None
        assert len(json_task.name) == 1000
        assert len(sqlite_task.name) == 1000
        assert len(json_task.details) == 10000
        assert len(sqlite_task.details) == 10000
        assert json_task.name == sqlite_task.name
        assert json_task.details == sqlite_task.details
