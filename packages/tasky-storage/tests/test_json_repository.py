import tempfile
from pathlib import Path
from uuid import uuid4

from tasky_storage import JsonTaskRepository
from tasky_tasks.models import TaskModel, TaskStatus


class TestJsonTaskRepository:
    def test_initialize_creates_empty_document(self):
        """Test that initialize creates an empty task document."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir) / "tasks.json"
            repo = JsonTaskRepository.from_path(storage_path)

            repo.initialize()

            tasks = repo.get_all_tasks()
            assert len(tasks) == 0

    def test_save_and_get_task(self):
        """Test saving and retrieving a task."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir) / "tasks.json"
            repo = JsonTaskRepository.from_path(storage_path)

            repo.initialize()

            # Create and save a task
            task = TaskModel(name="Test Task", details="Test details")
            repo.save_task(task)

            # Retrieve the task
            retrieved = repo.get_task(task.task_id)
            assert retrieved is not None
            assert retrieved.task_id == task.task_id
            assert retrieved.name == "Test Task"
            assert retrieved.details == "Test details"
            assert retrieved.status == TaskStatus.PENDING

    def test_get_nonexistent_task_returns_none(self):
        """Test that getting a non-existent task returns None."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir) / "tasks.json"
            repo = JsonTaskRepository.from_path(storage_path)

            repo.initialize()

            nonexistent_id = uuid4()
            task = repo.get_task(nonexistent_id)
            assert task is None

    def test_get_all_tasks(self):
        """Test retrieving all tasks."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir) / "tasks.json"
            repo = JsonTaskRepository.from_path(storage_path)

            repo.initialize()

            # Create multiple tasks
            task1 = TaskModel(name="Task 1", details="Details 1")
            task2 = TaskModel(name="Task 2", details="Details 2")

            repo.save_task(task1)
            repo.save_task(task2)

            # Get all tasks
            all_tasks = repo.get_all_tasks()
            assert len(all_tasks) == 2

            task_ids = {t.task_id for t in all_tasks}
            assert task1.task_id in task_ids
            assert task2.task_id in task_ids

    def test_update_task(self):
        """Test updating an existing task."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir) / "tasks.json"
            repo = JsonTaskRepository.from_path(storage_path)

            repo.initialize()

            # Create and save a task
            task = TaskModel(name="Original Name", details="Original details")
            repo.save_task(task)

            # Update the task
            task.name = "Updated Name"
            task.details = "Updated details"
            task.status = TaskStatus.COMPLETED
            repo.save_task(task)

            # Verify the update
            retrieved = repo.get_task(task.task_id)
            assert retrieved is not None
            assert retrieved.name == "Updated Name"
            assert retrieved.details == "Updated details"
            assert retrieved.status == TaskStatus.COMPLETED

    def test_delete_task(self):
        """Test deleting a task."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir) / "tasks.json"
            repo = JsonTaskRepository.from_path(storage_path)

            repo.initialize()

            # Create and save a task
            task = TaskModel(name="Task to Delete", details="Will be deleted")
            repo.save_task(task)

            # Verify it exists
            assert repo.task_exists(task.task_id)

            # Delete the task
            deleted = repo.delete_task(task.task_id)
            assert deleted is True

            # Verify it's gone
            assert not repo.task_exists(task.task_id)
            assert repo.get_task(task.task_id) is None

    def test_delete_nonexistent_task(self):
        """Test deleting a non-existent task."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir) / "tasks.json"
            repo = JsonTaskRepository.from_path(storage_path)

            repo.initialize()

            nonexistent_id = uuid4()
            deleted = repo.delete_task(nonexistent_id)
            assert deleted is False

    def test_task_exists(self):
        """Test checking if a task exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir) / "tasks.json"
            repo = JsonTaskRepository.from_path(storage_path)

            repo.initialize()

            # Create a task
            task = TaskModel(name="Existing Task", details="Exists")
            repo.save_task(task)

            # Check existence
            assert repo.task_exists(task.task_id)
            assert not repo.task_exists(uuid4())
