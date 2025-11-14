"""Task import/export functionality with JSON schema validation.

This module provides services for exporting tasks to JSON and importing them back
with support for multiple merge strategies (append, replace, merge).
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from tasky_logging import get_logger  # type: ignore[import-untyped]

from tasky_tasks.exceptions import (
    ExportError,
    IncompatibleVersionError,
    InvalidExportFormatError,
)
from tasky_tasks.models import TaskModel, TaskStatus

if TYPE_CHECKING:
    from tasky_tasks.service import TaskService


logger: logging.Logger = get_logger("tasks.export")  # type: ignore[no-untyped-call]


class TaskSnapshot(BaseModel):
    """Snapshot of a task for export/import.

    This represents a task in the portable JSON format used for import/export.
    All fields are required to ensure complete task data preservation.
    """

    task_id: UUID = Field(..., description="Task ID")
    name: str = Field(..., description="Task name")
    details: str = Field(..., description="Task details")
    status: TaskStatus = Field(..., description="Task status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class ExportDocument(BaseModel):
    """Export file structure with versioning and metadata.

    The version field enables forward compatibility by allowing future versions
    to detect and handle older export formats appropriately.
    """

    version: str = Field("1.0", description="Export format version")
    exported_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=UTC),
        description="Export timestamp",
    )
    source_project: str = Field("default", description="Source project identifier")
    task_count: int = Field(..., description="Number of tasks exported")
    tasks: list[TaskSnapshot] = Field(default_factory=list, description="Task list")


class ImportResult(BaseModel):
    """Result of import operation with detailed statistics.

    Provides comprehensive feedback about what happened during import,
    including counts of created, updated, and skipped tasks, plus any errors.
    """

    total_processed: int = Field(..., description="Total tasks processed")
    created: int = Field(0, description="Number of tasks created")
    updated: int = Field(0, description="Number of tasks updated")
    skipped: int = Field(0, description="Number of tasks skipped")
    errors: list[str] = Field(default_factory=list, description="Import errors")


class TaskImportExportService:
    """Service for importing and exporting tasks.

    This service handles the complete import/export lifecycle including:
    - JSON serialization and deserialization
    - Schema validation
    - Multiple import strategies (append, replace, merge)
    - Dry-run preview mode
    """

    # Supported format version
    CURRENT_VERSION = "1.0"

    def __init__(self, task_service: TaskService) -> None:
        """Initialize the import/export service.

        Parameters
        ----------
        task_service:
            The task service for accessing and modifying tasks.

        """
        self.task_service = task_service

    def export_tasks(
        self,
        file_path: Path,
        *,
        project_name: str = "default",
    ) -> ExportDocument:
        """Export all tasks to a JSON file.

        Parameters
        ----------
        file_path:
            Path where the JSON export file will be written.
        project_name:
            Name of the source project (for metadata only).

        Returns
        -------
        ExportDocument:
            The exported document containing all tasks and metadata.

        Raises
        ------
        ExportError:
            Raised when export fails due to file I/O or serialization errors.

        """
        logger.info("Starting task export to: %s", file_path)

        try:
            # Fetch all tasks
            tasks = self.task_service.get_all_tasks()
            logger.debug("Fetched %d tasks for export", len(tasks))

            # Convert to snapshots
            snapshots = [self._task_to_snapshot(task) for task in tasks]

            # Create export document
            export_doc = ExportDocument(
                version=self.CURRENT_VERSION,
                source_project=project_name,
                task_count=len(snapshots),
                tasks=snapshots,
            )

            # Write to file
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with file_path.open("w", encoding="utf-8") as f:
                json.dump(
                    export_doc.model_dump(mode="json"),
                    f,
                    indent=2,
                    ensure_ascii=False,
                    default=str,
                )
        except OSError as exc:
            msg = f"Failed to write export file: {exc}"
            logger.exception(msg)
            raise ExportError(msg) from exc
        except Exception as exc:
            msg = f"Export failed: {exc}"
            logger.exception(msg)
            raise ExportError(msg) from exc
        else:
            logger.info("Successfully exported %d tasks to: %s", len(snapshots), file_path)
            return export_doc

    def import_tasks(
        self,
        file_path: Path,
        *,
        strategy: str = "append",
        dry_run: bool = False,
    ) -> ImportResult:
        """Import tasks from a JSON file.

        Parameters
        ----------
        file_path:
            Path to the JSON export file to import.
        strategy:
            Import strategy: 'append', 'replace', or 'merge'.
        dry_run:
            If True, simulate the import without making changes.

        Returns
        -------
        ImportResult:
            Statistics about the import operation.

        Raises
        ------
        ImportError:
            Raised when import fails due to invalid file or data.
        InvalidExportFormatError:
            Raised when the JSON file is malformed or missing required fields.
        IncompatibleVersionError:
            Raised when the export format version is not supported.

        """
        logger.info(
            "Starting task import from: %s (strategy=%s, dry_run=%s)",
            file_path,
            strategy,
            dry_run,
        )

        # Load and validate the export document
        export_doc = self._load_and_validate(file_path)

        # Apply the selected strategy
        if strategy == "append":
            result = self._apply_append_strategy(export_doc, dry_run=dry_run)
        elif strategy == "replace":
            result = self._apply_replace_strategy(export_doc, dry_run=dry_run)
        elif strategy == "merge":
            result = self._apply_merge_strategy(export_doc, dry_run=dry_run)
        else:
            msg = f"Invalid import strategy: {strategy}"
            raise ImportError(msg)

        action = "Would import" if dry_run else "Imported"
        logger.info(
            "%s %d tasks: created=%d, updated=%d, skipped=%d",
            action,
            result.total_processed,
            result.created,
            result.updated,
            result.skipped,
        )

        return result

    def _load_and_validate(self, file_path: Path) -> ExportDocument:
        """Load and validate an export document from a JSON file.

        Parameters
        ----------
        file_path:
            Path to the JSON export file.

        Returns
        -------
        ExportDocument:
            The validated export document.

        Raises
        ------
        ImportError:
            Raised when the file cannot be read.
        InvalidExportFormatError:
            Raised when the JSON is malformed or validation fails.
        IncompatibleVersionError:
            Raised when the format version is not supported.

        """
        try:
            with file_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except OSError as exc:
            msg = f"Failed to read import file: {exc}"
            logger.exception(msg)
            raise ImportError(msg) from exc
        except json.JSONDecodeError as exc:
            msg = f"Invalid JSON in import file: {exc}"
            logger.exception(msg)
            raise InvalidExportFormatError(msg) from exc

        # Validate against schema
        try:
            export_doc = ExportDocument.model_validate(data)
        except Exception as exc:
            msg = f"Invalid export format: {exc}"
            logger.exception(msg)
            raise InvalidExportFormatError(msg) from exc

        # Check version compatibility
        if export_doc.version != self.CURRENT_VERSION:
            msg = (
                f"Incompatible export version: {export_doc.version} "
                f"(expected {self.CURRENT_VERSION})"
            )
            logger.error(msg)
            raise IncompatibleVersionError(
                msg,
                expected=self.CURRENT_VERSION,
                actual=export_doc.version,
            )

        logger.debug(
            "Loaded and validated export document: version=%s, tasks=%d",
            export_doc.version,
            export_doc.task_count,
        )
        return export_doc

    def _apply_append_strategy(self, export_doc: ExportDocument, *, dry_run: bool) -> ImportResult:
        """Apply append strategy: add all tasks, re-key duplicates.

        Parameters
        ----------
        export_doc:
            The export document containing tasks to import.
        dry_run:
            If True, simulate without making changes.

        Returns
        -------
        ImportResult:
            Statistics about the import operation.

        """
        created_count = 0
        errors: list[str] = []

        # Get existing task IDs
        existing_tasks = self.task_service.get_all_tasks()
        existing_ids = {task.task_id for task in existing_tasks}

        for snapshot in export_doc.tasks:
            try:
                task = self._snapshot_to_task(snapshot)

                # Re-key if ID already exists
                if task.task_id in existing_ids:
                    old_id = task.task_id
                    task.task_id = uuid4()
                    logger.debug("Re-keyed duplicate task: %s -> %s", old_id, task.task_id)

                if not dry_run:
                    self.task_service.repository.save_task(task)

                created_count += 1
                existing_ids.add(task.task_id)  # Track for subsequent imports in same batch

            except Exception as exc:  # noqa: BLE001  # Catch all to continue batch import
                error_msg = f"Failed to import task '{snapshot.task_id}': {exc}"
                logger.warning(error_msg)
                errors.append(error_msg)

        return ImportResult(
            total_processed=len(export_doc.tasks),
            created=created_count,
            updated=0,
            skipped=len(errors),
            errors=errors,
        )

    def _apply_replace_strategy(self, export_doc: ExportDocument, *, dry_run: bool) -> ImportResult:
        """Apply replace strategy: clear all existing tasks, then import.

        Parameters
        ----------
        export_doc:
            The export document containing tasks to import.
        dry_run:
            If True, simulate without making changes.

        Returns
        -------
        ImportResult:
            Statistics about the import operation.

        """
        # Clear all existing tasks
        self._clear_existing_tasks(dry_run=dry_run)

        # Import all tasks from export
        return self._import_task_batch(export_doc, dry_run=dry_run)

    def _apply_merge_strategy(self, export_doc: ExportDocument, *, dry_run: bool) -> ImportResult:
        """Apply merge strategy: update existing by ID, create new ones.

        Parameters
        ----------
        export_doc:
            The export document containing tasks to import.
        dry_run:
            If True, simulate without making changes.

        Returns
        -------
        ImportResult:
            Statistics about the import operation.

        """
        created_count = 0
        updated_count = 0
        errors: list[str] = []

        # Get existing task IDs
        existing_tasks = self.task_service.get_all_tasks()
        existing_ids = {task.task_id for task in existing_tasks}

        for snapshot in export_doc.tasks:
            try:
                task = self._snapshot_to_task(snapshot)
                is_update = task.task_id in existing_ids

                if not dry_run:
                    self.task_service.repository.save_task(task)

                if is_update:
                    updated_count += 1
                    logger.debug("Updated existing task: %s", task.task_id)
                else:
                    created_count += 1
                    logger.debug("Created new task: %s", task.task_id)

            except Exception as exc:  # noqa: BLE001  # Catch all to continue batch import
                error_msg = f"Failed to import task '{snapshot.task_id}': {exc}"
                logger.warning(error_msg)
                errors.append(error_msg)

        return ImportResult(
            total_processed=len(export_doc.tasks),
            created=created_count,
            updated=updated_count,
            skipped=len(errors),
            errors=errors,
        )

    def _task_to_snapshot(self, task: TaskModel) -> TaskSnapshot:
        """Convert a TaskModel to a TaskSnapshot for export.

        Parameters
        ----------
        task:
            The task model to convert.

        Returns
        -------
        TaskSnapshot:
            The task snapshot for export.

        """
        return TaskSnapshot(
            task_id=task.task_id,
            name=task.name,
            details=task.details,
            status=task.status,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )

    def _clear_existing_tasks(self, *, dry_run: bool) -> None:
        """Clear all existing tasks (used by replace strategy).

        Parameters
        ----------
        dry_run:
            If True, simulate without making changes.

        """
        if not dry_run:
            existing_tasks = self.task_service.get_all_tasks()
            for task in existing_tasks:
                self.task_service.repository.delete_task(task.task_id)
            logger.info("Cleared %d existing tasks", len(existing_tasks))

    def _import_task_batch(
        self,
        export_doc: ExportDocument,
        *,
        dry_run: bool,
    ) -> ImportResult:
        """Import a batch of tasks (create only).

        Parameters
        ----------
        export_doc:
            The export document containing tasks to import.
        dry_run:
            If True, simulate without making changes.

        Returns
        -------
        ImportResult:
            Statistics about the import operation.

        """
        created_count = 0
        errors: list[str] = []

        for snapshot in export_doc.tasks:
            try:
                task = self._snapshot_to_task(snapshot)
                if not dry_run:
                    self.task_service.repository.save_task(task)
                created_count += 1
            except Exception as exc:  # noqa: BLE001  # Catch all to continue batch import
                error_msg = f"Failed to import task '{snapshot.task_id}': {exc}"
                logger.warning(error_msg)
                errors.append(error_msg)

        return ImportResult(
            total_processed=len(export_doc.tasks),
            created=created_count,
            updated=0,
            skipped=len(errors),
            errors=errors,
        )

    def _snapshot_to_task(self, snapshot: TaskSnapshot) -> TaskModel:
        """Convert a TaskSnapshot to a TaskModel for import.

        Parameters
        ----------
        snapshot:
            The task snapshot to convert.

        Returns
        -------
        TaskModel:
            The task model for import.

        """
        return TaskModel(
            task_id=snapshot.task_id,
            name=snapshot.name,
            details=snapshot.details,
            status=snapshot.status,
            created_at=snapshot.created_at,
            updated_at=snapshot.updated_at,
        )
