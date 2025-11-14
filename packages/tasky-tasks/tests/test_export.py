"""Tests for task import/export functionality."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from tasky_storage.backends.json.repository import JsonTaskRepository
from tasky_storage.backends.json.storage import JsonStorage
from tasky_tasks.exceptions import (
    ExportError,
    IncompatibleVersionError,
    InvalidExportFormatError,
    TaskImportError,
)
from tasky_tasks.export import (
    ExportDocument,
    ImportResult,
    TaskImportExportService,
    TaskSnapshot,
)
from tasky_tasks.models import TaskModel, TaskStatus
from tasky_tasks.service import TaskService


@pytest.fixture
def task_service(tmp_path: Path) -> TaskService:
    """Create a task service with JSON backend for testing."""
    storage = JsonStorage(path=tmp_path / "test_tasks.json")
    repository = JsonTaskRepository(storage=storage)
    repository.initialize()
    return TaskService(repository)


@pytest.fixture
def export_service(task_service: TaskService) -> TaskImportExportService:
    """Create an import/export service for testing."""
    return TaskImportExportService(task_service)


@pytest.fixture
def sample_task() -> TaskModel:
    """Create a sample task for testing."""
    return TaskModel(
        task_id=UUID("12345678-1234-5678-1234-567812345678"),
        name="Test Task",
        details="Test details",
        status=TaskStatus.PENDING,
        created_at=datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC),
        updated_at=datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC),
    )


class TestTaskSnapshot:
    """Tests for TaskSnapshot model."""

    def test_task_snapshot_creation(self, sample_task: TaskModel) -> None:
        """Test creating a task snapshot."""
        snapshot = TaskSnapshot(
            task_id=sample_task.task_id,
            name=sample_task.name,
            details=sample_task.details,
            status=sample_task.status,
            created_at=sample_task.created_at,
            updated_at=sample_task.updated_at,
        )

        assert snapshot.task_id == sample_task.task_id
        assert snapshot.name == sample_task.name
        assert snapshot.details == sample_task.details
        assert snapshot.status == sample_task.status
        assert snapshot.created_at == sample_task.created_at
        assert snapshot.updated_at == sample_task.updated_at


class TestExportDocument:
    """Tests for ExportDocument model."""

    def test_export_document_creation(self) -> None:
        """Test creating an export document."""
        doc = ExportDocument(
            version="1.0",
            source_project="test-project",
            task_count=1,
            tasks=[],
        )

        assert doc.version == "1.0"
        assert doc.source_project == "test-project"
        assert doc.task_count == 1
        assert doc.tasks == []

    def test_export_document_defaults(self) -> None:
        """Test export document with default values."""
        doc = ExportDocument(task_count=0)

        assert doc.version == "1.0"
        assert doc.source_project == "default"
        assert isinstance(doc.exported_at, datetime)
        assert doc.tasks == []


class TestImportResult:
    """Tests for ImportResult model."""

    def test_import_result_creation(self) -> None:
        """Test creating an import result."""
        result = ImportResult(
            total_processed=10,
            created=5,
            updated=3,
            skipped=2,
            errors=["Error 1", "Error 2"],
        )

        assert result.total_processed == 10
        assert result.created == 5
        assert result.updated == 3
        assert result.skipped == 2
        assert result.errors == ["Error 1", "Error 2"]


class TestExportTasks:
    """Tests for task export functionality."""

    def test_export_empty_task_list(
        self,
        export_service: TaskImportExportService,
        tmp_path: Path,
    ) -> None:
        """Test exporting when there are no tasks."""
        export_file = tmp_path / "export.json"
        doc = export_service.export_tasks(export_file, project_name="test")

        assert doc.task_count == 0
        assert doc.tasks == []
        assert doc.source_project == "test"
        assert export_file.exists()

    def test_export_single_task(
        self,
        task_service: TaskService,
        export_service: TaskImportExportService,
        sample_task: TaskModel,
        tmp_path: Path,
    ) -> None:
        """Test exporting a single task."""
        # Create a task
        created = task_service.create_task(
            name=sample_task.name,
            details=sample_task.details,
        )

        # Export it
        export_file = tmp_path / "export.json"
        doc = export_service.export_tasks(export_file)

        assert doc.task_count == 1
        assert len(doc.tasks) == 1
        assert doc.tasks[0].task_id == created.task_id
        assert doc.tasks[0].name == created.name
        assert doc.tasks[0].details == created.details

        # Verify file contents
        with export_file.open("r") as f:
            data = json.load(f)
        assert data["task_count"] == 1
        assert len(data["tasks"]) == 1

    def test_export_multiple_tasks(
        self,
        task_service: TaskService,
        export_service: TaskImportExportService,
        tmp_path: Path,
    ) -> None:
        """Test exporting multiple tasks."""
        # Create tasks
        task1 = task_service.create_task("Task 1", "Details 1")
        task2 = task_service.create_task("Task 2", "Details 2")
        task3 = task_service.create_task("Task 3", "Details 3")

        # Export them
        export_file = tmp_path / "export.json"
        doc = export_service.export_tasks(export_file)

        assert doc.task_count == 3
        assert len(doc.tasks) == 3

        # Verify all task IDs are present
        exported_ids = {t.task_id for t in doc.tasks}
        assert task1.task_id in exported_ids
        assert task2.task_id in exported_ids
        assert task3.task_id in exported_ids

    def test_export_creates_parent_directories(
        self,
        export_service: TaskImportExportService,
        tmp_path: Path,
    ) -> None:
        """Test that export creates parent directories if needed."""
        export_file = tmp_path / "nested" / "dir" / "export.json"
        assert not export_file.parent.exists()

        export_service.export_tasks(export_file)

        assert export_file.exists()
        assert export_file.parent.exists()

    def test_export_overwrites_existing_file(
        self,
        task_service: TaskService,
        export_service: TaskImportExportService,
        tmp_path: Path,
    ) -> None:
        """Test that export overwrites an existing file."""
        export_file = tmp_path / "export.json"

        # First export (no tasks)
        doc1 = export_service.export_tasks(export_file)
        assert doc1.task_count == 0

        # Create a task
        task_service.create_task("New Task", "New Details")

        # Second export (1 task)
        doc2 = export_service.export_tasks(export_file)
        assert doc2.task_count == 1

    def test_export_handles_file_write_error(
        self,
        export_service: TaskImportExportService,
        tmp_path: Path,
    ) -> None:
        """Test that export raises ExportError when file write fails."""
        # Try to write to a directory instead of a file
        invalid_path = tmp_path / "invalid"
        invalid_path.mkdir()

        with pytest.raises(ExportError, match="Failed to write export file"):
            export_service.export_tasks(invalid_path)


class TestImportTasks:
    """Tests for task import functionality."""

    def test_import_from_nonexistent_file(
        self,
        export_service: TaskImportExportService,
        tmp_path: Path,
    ) -> None:
        """Test importing from a file that doesn't exist."""
        nonexistent = tmp_path / "nonexistent.json"

        with pytest.raises(TaskImportError, match="File not found"):
            export_service.import_tasks(nonexistent)

    def test_import_invalid_json(
        self,
        export_service: TaskImportExportService,
        tmp_path: Path,
    ) -> None:
        """Test importing from a file with invalid JSON."""
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("{ invalid json }")

        with pytest.raises(InvalidExportFormatError, match="Invalid JSON"):
            export_service.import_tasks(invalid_file)

    def test_import_missing_required_fields(
        self,
        export_service: TaskImportExportService,
        tmp_path: Path,
    ) -> None:
        """Test importing from a file missing required fields."""
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text('{"version": "1.0"}')  # Missing task_count

        with pytest.raises(InvalidExportFormatError, match="Invalid export format"):
            export_service.import_tasks(invalid_file)

    def test_import_incompatible_version(
        self,
        export_service: TaskImportExportService,
        tmp_path: Path,
    ) -> None:
        """Test importing from a file with incompatible version."""
        invalid_file = tmp_path / "invalid.json"
        data = {
            "version": "999.0",
            "task_count": 0,
            "tasks": [],
        }
        invalid_file.write_text(json.dumps(data))

        with pytest.raises(IncompatibleVersionError, match="Incompatible export version"):
            export_service.import_tasks(invalid_file)

    def test_import_append_strategy(
        self,
        task_service: TaskService,
        export_service: TaskImportExportService,
        tmp_path: Path,
    ) -> None:
        """Test importing with append strategy."""
        # Create an existing task
        _ = task_service.create_task("Existing", "Details")

        # Create an export with a new task
        export_file = tmp_path / "import.json"
        new_task = TaskSnapshot(
            task_id=uuid4(),
            name="New Task",
            details="New Details",
            status=TaskStatus.PENDING,
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )
        doc = ExportDocument(task_count=1, tasks=[new_task])
        export_file.write_text(json.dumps(doc.model_dump(mode="json"), default=str))

        # Import with append strategy
        result = export_service.import_tasks(export_file, strategy="append")

        assert result.total_processed == 1
        assert result.created == 1
        assert result.updated == 0
        assert result.skipped == 0

        # Verify both tasks exist
        all_tasks = task_service.get_all_tasks()
        assert len(all_tasks) == 2

    def test_import_replace_strategy(
        self,
        task_service: TaskService,
        export_service: TaskImportExportService,
        tmp_path: Path,
    ) -> None:
        """Test importing with replace strategy."""
        # Create existing tasks
        task_service.create_task("Existing 1", "Details 1")
        task_service.create_task("Existing 2", "Details 2")

        # Create an export with a single new task
        export_file = tmp_path / "import.json"
        new_task = TaskSnapshot(
            task_id=uuid4(),
            name="New Task",
            details="New Details",
            status=TaskStatus.PENDING,
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )
        doc = ExportDocument(task_count=1, tasks=[new_task])
        export_file.write_text(json.dumps(doc.model_dump(mode="json"), default=str))

        # Import with replace strategy
        result = export_service.import_tasks(export_file, strategy="replace")

        assert result.total_processed == 1
        assert result.created == 1

        # Verify only the new task exists
        all_tasks = task_service.get_all_tasks()
        assert len(all_tasks) == 1
        assert all_tasks[0].name == "New Task"

    def test_import_merge_strategy_creates_new(
        self,
        export_service: TaskImportExportService,
        tmp_path: Path,
    ) -> None:
        """Test importing with merge strategy creates new tasks."""
        # Create an export with a new task
        export_file = tmp_path / "import.json"
        new_task = TaskSnapshot(
            task_id=uuid4(),
            name="New Task",
            details="New Details",
            status=TaskStatus.PENDING,
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )
        doc = ExportDocument(task_count=1, tasks=[new_task])
        export_file.write_text(json.dumps(doc.model_dump(mode="json"), default=str))

        # Import with merge strategy
        result = export_service.import_tasks(export_file, strategy="merge")

        assert result.total_processed == 1
        assert result.created == 1
        assert result.updated == 0

    def test_import_merge_strategy_updates_existing(
        self,
        task_service: TaskService,
        export_service: TaskImportExportService,
        tmp_path: Path,
    ) -> None:
        """Test importing with merge strategy updates existing tasks."""
        # Create an existing task
        existing = task_service.create_task("Original Name", "Original Details")

        # Create an export with the same task ID but different data
        export_file = tmp_path / "import.json"
        updated_task = TaskSnapshot(
            task_id=existing.task_id,
            name="Updated Name",
            details="Updated Details",
            status=TaskStatus.COMPLETED,
            created_at=existing.created_at,
            updated_at=datetime.now(tz=UTC),
        )
        doc = ExportDocument(task_count=1, tasks=[updated_task])
        export_file.write_text(json.dumps(doc.model_dump(mode="json"), default=str))

        # Import with merge strategy
        result = export_service.import_tasks(export_file, strategy="merge")

        assert result.total_processed == 1
        assert result.created == 0
        assert result.updated == 1

        # Verify task was updated
        task = task_service.get_task(existing.task_id)
        assert task.name == "Updated Name"
        assert task.details == "Updated Details"
        assert task.status == TaskStatus.COMPLETED

    def test_import_dry_run_does_not_modify(
        self,
        task_service: TaskService,
        export_service: TaskImportExportService,
        tmp_path: Path,
    ) -> None:
        """Test that dry run doesn't actually import tasks."""
        # Create an export with a new task
        export_file = tmp_path / "import.json"
        new_task = TaskSnapshot(
            task_id=uuid4(),
            name="New Task",
            details="New Details",
            status=TaskStatus.PENDING,
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )
        doc = ExportDocument(task_count=1, tasks=[new_task])
        export_file.write_text(json.dumps(doc.model_dump(mode="json"), default=str))

        # Import with dry run
        result = export_service.import_tasks(export_file, strategy="append", dry_run=True)

        assert result.total_processed == 1
        assert result.created == 1

        # Verify no tasks were actually created
        all_tasks = task_service.get_all_tasks()
        assert len(all_tasks) == 0

    def test_import_invalid_strategy(
        self,
        export_service: TaskImportExportService,
        tmp_path: Path,
    ) -> None:
        """Test importing with an invalid strategy."""
        export_file = tmp_path / "import.json"
        doc = ExportDocument(task_count=0, tasks=[])
        export_file.write_text(json.dumps(doc.model_dump(mode="json"), default=str))

        with pytest.raises(TaskImportError, match="Invalid import strategy"):
            export_service.import_tasks(export_file, strategy="invalid")


class TestRoundTripImportExport:
    """Tests for round-trip import/export."""

    def test_export_then_import_preserves_data(
        self,
        task_service: TaskService,
        export_service: TaskImportExportService,
        tmp_path: Path,
    ) -> None:
        """Test that exporting then importing preserves all task data."""
        # Create tasks with various states
        task1 = task_service.create_task("Task 1", "Details 1")
        task2 = task_service.create_task("Task 2", "Details 2")
        task_service.complete_task(task2.task_id)
        task3 = task_service.create_task("Task 3", "Details 3")
        task_service.cancel_task(task3.task_id)

        # Export
        export_file = tmp_path / "export.json"
        export_service.export_tasks(export_file)

        # Clear all tasks
        for task in task_service.get_all_tasks():
            task_service.delete_task(task.task_id)
        assert len(task_service.get_all_tasks()) == 0

        # Import
        result = export_service.import_tasks(export_file, strategy="append")

        assert result.total_processed == 3
        assert result.created == 3

        # Verify all tasks were restored
        restored_tasks = task_service.get_all_tasks()
        assert len(restored_tasks) == 3

        # Verify task data
        task_map = {t.task_id: t for t in restored_tasks}
        assert task_map[task1.task_id].name == "Task 1"
        assert task_map[task1.task_id].status == TaskStatus.PENDING
        assert task_map[task2.task_id].status == TaskStatus.COMPLETED
        assert task_map[task3.task_id].status == TaskStatus.CANCELLED
