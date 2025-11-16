"""Integration tests for backend migration scenarios."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest
from tasky_storage import JsonTaskRepository, SqliteTaskRepository
from tasky_tasks.models import TaskModel, TaskStatus


class TestBackendMigration:
    """Test data integrity during backend switching."""

    def test_json_to_sqlite_migration(self, tmp_path: Path) -> None:
        """Test migrating tasks from JSON to SQLite backend."""
        json_path = tmp_path / "tasks.json"
        sqlite_path = tmp_path / "tasks.db"

        # Create JSON repository and add tasks
        json_repo = JsonTaskRepository.from_path(json_path)
        json_repo.initialize()

        tasks = [
            TaskModel(name=f"Task {i}", details=f"Details {i}")
            for i in range(10)
        ]
        for task in tasks:
            json_repo.save_task(task)

        # Migrate to SQLite
        sqlite_repo = SqliteTaskRepository.from_path(sqlite_path)

        # Copy all tasks from JSON to SQLite
        json_tasks = json_repo.get_all_tasks()
        for task in json_tasks:
            sqlite_repo.save_task(task)

        # Verify all tasks migrated correctly
        sqlite_tasks = sqlite_repo.get_all_tasks()
        assert len(sqlite_tasks) == 10

        # Verify task data integrity
        for original_task in tasks:
            migrated_task = sqlite_repo.get_task(original_task.task_id)
            assert migrated_task is not None
            assert migrated_task.task_id == original_task.task_id
            assert migrated_task.name == original_task.name
            assert migrated_task.details == original_task.details
            assert migrated_task.status == original_task.status

    def test_sqlite_to_json_migration(self, tmp_path: Path) -> None:
        """Test migrating tasks from SQLite to JSON backend."""
        sqlite_path = tmp_path / "tasks.db"
        json_path = tmp_path / "tasks.json"

        # Create SQLite repository and add tasks
        sqlite_repo = SqliteTaskRepository.from_path(sqlite_path)

        tasks = [
            TaskModel(name=f"Task {i}", details=f"Details {i}")
            for i in range(10)
        ]
        for task in tasks:
            sqlite_repo.save_task(task)

        # Migrate to JSON
        json_repo = JsonTaskRepository.from_path(json_path)
        json_repo.initialize()

        # Copy all tasks from SQLite to JSON
        sqlite_tasks = sqlite_repo.get_all_tasks()
        for task in sqlite_tasks:
            json_repo.save_task(task)

        # Verify all tasks migrated correctly
        json_tasks = json_repo.get_all_tasks()
        assert len(json_tasks) == 10

        # Verify task data integrity
        for original_task in tasks:
            migrated_task = json_repo.get_task(original_task.task_id)
            assert migrated_task is not None
            assert migrated_task.task_id == original_task.task_id
            assert migrated_task.name == original_task.name
            assert migrated_task.details == original_task.details
            assert migrated_task.status == original_task.status

    def test_json_to_sqlite_round_trip(self, tmp_path: Path) -> None:
        """Test round-trip migration: JSON -> SQLite -> JSON."""
        json_path1 = tmp_path / "tasks1.json"
        sqlite_path = tmp_path / "tasks.db"
        json_path2 = tmp_path / "tasks2.json"

        # Create initial JSON repository
        json_repo1 = JsonTaskRepository.from_path(json_path1)
        json_repo1.initialize()

        tasks = [
            TaskModel(name=f"Task {i}", details=f"Details {i}")
            for i in range(20)
        ]
        for task in tasks:
            json_repo1.save_task(task)

        # Migrate to SQLite
        sqlite_repo = SqliteTaskRepository.from_path(sqlite_path)
        json_tasks = json_repo1.get_all_tasks()
        for task in json_tasks:
            sqlite_repo.save_task(task)

        # Migrate back to JSON
        json_repo2 = JsonTaskRepository.from_path(json_path2)
        json_repo2.initialize()
        sqlite_tasks = sqlite_repo.get_all_tasks()
        for task in sqlite_tasks:
            json_repo2.save_task(task)

        # Verify round-trip integrity
        final_tasks = json_repo2.get_all_tasks()
        assert len(final_tasks) == 20

        for original_task in tasks:
            final_task = json_repo2.get_task(original_task.task_id)
            assert final_task is not None
            assert final_task.task_id == original_task.task_id
            assert final_task.name == original_task.name
            assert final_task.details == original_task.details
            assert final_task.status == original_task.status

    def test_large_dataset_migration(self, tmp_path: Path) -> None:
        """Test migration with 1000+ tasks."""
        json_path = tmp_path / "tasks.json"
        sqlite_path = tmp_path / "tasks.db"

        # Create JSON repository with many tasks
        json_repo = JsonTaskRepository.from_path(json_path)
        json_repo.initialize()

        # Create 1000 tasks
        tasks = [
            TaskModel(
                name=f"Task {i}",
                details=f"Details for task {i}",
                status=TaskStatus.PENDING if i % 2 == 0 else TaskStatus.COMPLETED,
            )
            for i in range(1000)
        ]

        for task in tasks:
            json_repo.save_task(task)

        # Migrate to SQLite
        sqlite_repo = SqliteTaskRepository.from_path(sqlite_path)
        json_tasks = json_repo.get_all_tasks()
        assert len(json_tasks) == 1000

        for task in json_tasks:
            sqlite_repo.save_task(task)

        # Verify migration
        sqlite_tasks = sqlite_repo.get_all_tasks()
        assert len(sqlite_tasks) == 1000

        # Verify sample of tasks
        sample_indices = [0, 100, 500, 999]
        for idx in sample_indices:
            original_task = tasks[idx]
            migrated_task = sqlite_repo.get_task(original_task.task_id)
            assert migrated_task is not None
            assert migrated_task.task_id == original_task.task_id
            assert migrated_task.name == original_task.name
            assert migrated_task.status == original_task.status

    def test_migration_preserves_task_states(self, tmp_path: Path) -> None:
        """Test that migration preserves all task states correctly."""
        json_path = tmp_path / "tasks.json"
        sqlite_path = tmp_path / "tasks.db"

        # Create tasks with different states
        json_repo = JsonTaskRepository.from_path(json_path)
        json_repo.initialize()

        pending_task = TaskModel(name="Pending", details="Pending task")
        completed_task = TaskModel(name="Completed", details="Completed task")
        completed_task.complete()
        cancelled_task = TaskModel(name="Cancelled", details="Cancelled task")
        cancelled_task.cancel()

        json_repo.save_task(pending_task)
        json_repo.save_task(completed_task)
        json_repo.save_task(cancelled_task)

        # Migrate to SQLite
        sqlite_repo = SqliteTaskRepository.from_path(sqlite_path)
        json_tasks = json_repo.get_all_tasks()
        for task in json_tasks:
            sqlite_repo.save_task(task)

        # Verify states preserved
        sqlite_pending = sqlite_repo.get_task(pending_task.task_id)
        assert sqlite_pending is not None
        assert sqlite_pending.status == TaskStatus.PENDING

        sqlite_completed = sqlite_repo.get_task(completed_task.task_id)
        assert sqlite_completed is not None
        assert sqlite_completed.status == TaskStatus.COMPLETED

        sqlite_cancelled = sqlite_repo.get_task(cancelled_task.task_id)
        assert sqlite_cancelled is not None
        assert sqlite_cancelled.status == TaskStatus.CANCELLED

    def test_migration_preserves_timestamps(self, tmp_path: Path) -> None:
        """Test that migration preserves task timestamps."""
        json_path = tmp_path / "tasks.json"
        sqlite_path = tmp_path / "tasks.db"

        # Create task in JSON
        json_repo = JsonTaskRepository.from_path(json_path)
        json_repo.initialize()

        task = TaskModel(name="Timestamp Test", details="Testing timestamps")
        json_repo.save_task(task)

        # Get original timestamps
        original_task = json_repo.get_task(task.task_id)
        assert original_task is not None
        original_created = original_task.created_at
        original_updated = original_task.updated_at

        # Migrate to SQLite
        sqlite_repo = SqliteTaskRepository.from_path(sqlite_path)
        json_tasks = json_repo.get_all_tasks()
        for task in json_tasks:
            sqlite_repo.save_task(task)

        # Verify timestamps preserved
        migrated_task = sqlite_repo.get_task(task.task_id)
        assert migrated_task is not None
        assert migrated_task.created_at == original_created
        assert migrated_task.updated_at == original_updated

    def test_migration_handles_updated_tasks(self, tmp_path: Path) -> None:
        """Test that migration handles tasks that have been updated."""
        json_path = tmp_path / "tasks.json"
        sqlite_path = tmp_path / "tasks.db"

        # Create and update task in JSON
        json_repo = JsonTaskRepository.from_path(json_path)
        json_repo.initialize()

        task = TaskModel(name="Original", details="Original details")
        json_repo.save_task(task)

        task.name = "Updated"
        task.details = "Updated details"
        task.mark_updated()
        json_repo.save_task(task)

        # Migrate to SQLite
        sqlite_repo = SqliteTaskRepository.from_path(sqlite_path)
        json_tasks = json_repo.get_all_tasks()
        for task in json_tasks:
            sqlite_repo.save_task(task)

        # Verify updated task migrated correctly
        migrated_task = sqlite_repo.get_task(task.task_id)
        assert migrated_task is not None
        assert migrated_task.name == "Updated"
        assert migrated_task.details == "Updated details"

    def test_migration_filter_consistency(self, tmp_path: Path) -> None:
        """Test that filtering works consistently after migration."""
        from tasky_tasks.models import TaskFilter

        json_path = tmp_path / "tasks.json"
        sqlite_path = tmp_path / "tasks.db"

        # Create tasks with different statuses in JSON
        json_repo = JsonTaskRepository.from_path(json_path)
        json_repo.initialize()

        tasks = []
        for i in range(10):
            task = TaskModel(name=f"Task {i}", details=f"Details {i}")
            if i % 3 == 0:
                task.complete()
            elif i % 3 == 1:
                task.cancel()
            tasks.append(task)
            json_repo.save_task(task)

        # Migrate to SQLite
        sqlite_repo = SqliteTaskRepository.from_path(sqlite_path)
        json_tasks = json_repo.get_all_tasks()
        for task in json_tasks:
            sqlite_repo.save_task(task)

        # Test filtering consistency
        pending_filter = TaskFilter(statuses=[TaskStatus.PENDING])
        completed_filter = TaskFilter(statuses=[TaskStatus.COMPLETED])
        cancelled_filter = TaskFilter(statuses=[TaskStatus.CANCELLED])

        json_pending = json_repo.find_tasks(pending_filter)
        sqlite_pending = sqlite_repo.find_tasks(pending_filter)
        assert len(json_pending) == len(sqlite_pending)

        json_completed = json_repo.find_tasks(completed_filter)
        sqlite_completed = sqlite_repo.find_tasks(completed_filter)
        assert len(json_completed) == len(sqlite_completed)

        json_cancelled = json_repo.find_tasks(cancelled_filter)
        sqlite_cancelled = sqlite_repo.find_tasks(cancelled_filter)
        assert len(json_cancelled) == len(sqlite_cancelled)
