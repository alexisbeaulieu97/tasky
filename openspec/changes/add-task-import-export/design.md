# Design: Task Import/Export Functionality

**Change ID**: `add-task-import-export`
**Date**: 2025-11-12

## Overview

This design outlines the architecture and implementation approach for task import/export functionality. The system uses JSON as the portable format with Pydantic for schema validation, three distinct merge strategies to handle different import scenarios, and comprehensive error handling with user-friendly feedback.

## Architecture Decisions

### 1. Export Format: JSON with Version

**Decision**: Use JSON format with explicit version field for extensibility

**Rationale**:
- **Human-readable**: Users can inspect exported files in any text editor
- **Standard**: JSON is widely supported for integration with other tools
- **Versionable**: Version field allows future format changes without breaking existing exports
- **Portable**: Works on all platforms without dependencies
- **Safe**: No binary format risks or compatibility issues

**Structure**:
```json
{
  "version": "1.0",
  "exported_at": "2025-11-12T10:30:00Z",
  "source_project": "default",
  "task_count": 42,
  "tasks": [...]
}
```

**Alternatives Considered**:
- CSV: Loses nested structure and type information
- XML: More verbose, harder to parse
- Binary format: Not portable or human-readable
- SQLite dump: Not as portable as JSON

### 2. Schema Validation: Pydantic Models

**Decision**: Define export/import schemas as Pydantic models for runtime validation

**Rationale**:
- **Type safety**: Catch malformed JSON before processing
- **Clear errors**: Pydantic provides detailed validation error messages
- **Reusable**: Same schema for export and import
- **Extensible**: Easy to add optional fields in future versions

**Models**:
```python
# packages/tasky-tasks/src/tasky_tasks/export.py

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
from tasky_tasks.models import TaskStatus

class TaskSnapshot(BaseModel):
    """Snapshot of a task for export/import."""
    task_id: UUID = Field(..., description="Task ID")
    name: str = Field(..., description="Task name")
    details: str = Field(..., description="Task details")
    status: TaskStatus = Field(..., description="Task status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

class ExportDocument(BaseModel):
    """Export file structure."""
    version: str = Field("1.0", description="Export format version")
    exported_at: datetime = Field(default_factory=datetime.utcnow, description="Export timestamp")
    source_project: str = Field("default", description="Source project identifier")
    task_count: int = Field(..., description="Number of tasks exported")
    tasks: list[TaskSnapshot] = Field(default_factory=list, description="Task list")

class ImportResult(BaseModel):
    """Result of import operation."""
    total_processed: int = Field(..., description="Total tasks processed")
    created: int = Field(0, description="Number of tasks created")
    updated: int = Field(0, description="Number of tasks updated")
    skipped: int = Field(0, description="Number of tasks skipped")
    errors: list[str] = Field(default_factory=list, description="Import errors")
```

### 3. Import Strategies: Three-Method Approach

**Decision**: Implement three distinct strategies as separate methods with clear semantics

**Rationale**:
- **Separation of concerns**: Each strategy is independent and testable
- **Clear intent**: Method names express what happens (`append`, `replace`, `merge`)
- **Type safety**: Explicit parameter prevents accidental misuse
- **Extensibility**: Easy to add new strategies in future

**Strategy Definitions**:

#### Append Strategy (Default)
- **Behavior**: Adds imported tasks to existing tasks without modification
- **Duplicates**: If task ID exists, creates new task with generated ID (re-keying)
- **Use case**: Adding tasks from template, merging from another backup
- **Risk**: Possible duplicate tasks if task IDs overlap

```python
def _apply_append_strategy(
    self,
    existing_tasks: list[TaskModel],
    imported_tasks: list[TaskModel]
) -> ImportResult:
    """Append imported tasks to existing tasks."""
    result = ImportResult(total_processed=len(imported_tasks))
    existing_ids = {t.task_id for t in existing_tasks}

    for task in imported_tasks:
        if task.task_id in existing_ids:
            # Re-key: generate new ID
            task.task_id = uuid4()

        self.repository.save_task(task)
        result.created += 1

    return result
```

#### Replace Strategy
- **Behavior**: Clears all existing tasks, then imports
- **Duplicates**: Not possible; all existing data cleared first
- **Use case**: Full backup restore, migration between projects
- **Risk**: Permanent loss of existing tasks (mitigated by backup capability)

```python
def _apply_replace_strategy(
    self,
    existing_tasks: list[TaskModel],
    imported_tasks: list[TaskModel]
) -> ImportResult:
    """Replace all tasks with imported tasks."""
    result = ImportResult(total_processed=len(imported_tasks))

    # Delete all existing tasks
    for task in existing_tasks:
        self.repository.delete_task(task.task_id)

    # Import new tasks
    for task in imported_tasks:
        self.repository.save_task(task)
        result.created += 1

    return result
```

#### Merge Strategy
- **Behavior**: Updates existing tasks by ID, creates new ones
- **Duplicates**: If task ID exists, updates existing task; if not, creates new
- **Use case**: Syncing task list between instances, selective updates
- **Risk**: Overwrites existing task data silently (expected behavior with --strategy merge)

```python
def _apply_merge_strategy(
    self,
    existing_tasks: list[TaskModel],
    imported_tasks: list[TaskModel]
) -> ImportResult:
    """Merge imported tasks with existing, updating by ID."""
    result = ImportResult(total_processed=len(imported_tasks))
    existing_by_id = {t.task_id: t for t in existing_tasks}

    for imported_task in imported_tasks:
        if imported_task.task_id in existing_by_id:
            # Update existing task
            existing_task = existing_by_id[imported_task.task_id]
            existing_task.name = imported_task.name
            existing_task.details = imported_task.details
            existing_task.status = imported_task.status
            existing_task.updated_at = imported_task.updated_at
            self.repository.save_task(existing_task)
            result.updated += 1
        else:
            # Create new task
            self.repository.save_task(imported_task)
            result.created += 1

    return result
```

### 4. Export/Import Location: New Service Class

**Decision**: Create `TaskImportExportService` that orchestrates export/import operations

**Rationale**:
- **Single Responsibility**: Dedicated class for import/export logic
- **Separation**: Not part of core `TaskService`
- **Reusability**: Can be used by CLI, API, or other hosts
- **Testability**: Clear interface to mock in tests

**Package Location**: `packages/tasky-tasks/src/tasky_tasks/export.py`

### 5. Validation: Before Application

**Decision**: Validate entire import file before making any database changes

**Rationale**:
- **Atomicity**: Either entire import succeeds or fails; no partial updates
- **Safety**: Catch errors early before any data modification
- **User confidence**: Clear feedback on whether import will work
- **Dry-run support**: Can validate without applying

**Validation Steps**:
1. Parse JSON file
2. Validate against `ExportDocument` schema
3. Check version compatibility
4. Validate each task snapshot can be converted to `TaskModel`
5. Check for fatal conflicts (e.g., merge strategy with new tasks in pending only)

### 6. Dry-Run Mode: Preview Without Changes

**Decision**: Support `--dry-run` flag to preview import without applying

**Rationale**:
- **Safety**: Users can preview before applying
- **Debugging**: Helps understand what merge will do
- **Testing**: CLI can show preview exactly as it would apply

**Implementation**:
```python
def import_tasks(
    self,
    file_path: Path,
    strategy: ImportStrategy = ImportStrategy.APPEND,
    dry_run: bool = False
) -> ImportResult:
    """Import tasks from JSON file."""
    # Validate and parse
    document = self._load_and_validate(file_path)
    imported_tasks = [self._snapshot_to_model(s) for s in document.tasks]

    if dry_run:
        # Calculate result without applying
        return self._simulate_strategy(imported_tasks, strategy)
    else:
        # Apply strategy
        return self._apply_strategy(imported_tasks, strategy)
```

### 7. Error Handling: User-Friendly Messages

**Decision**: Catch all error types, convert to specific exceptions with context

**Rationale**:
- **Clarity**: Different errors get different treatment
- **User guidance**: Error messages suggest next steps
- **Debugging**: Context helps developers understand what went wrong

**Error Types**:
```python
class ImportExportError(Exception):
    """Base class for import/export errors."""
    pass

class ExportError(ImportExportError):
    """Raised when export operation fails."""
    pass

class ImportError(ImportExportError):
    """Raised when import operation fails."""
    pass

class InvalidExportFormatError(ImportError):
    """Raised when export file format is invalid."""
    pass

class IncompatibleVersionError(ImportError):
    """Raised when export version is incompatible."""
    pass

class TaskValidationError(ImportError):
    """Raised when imported task data is invalid."""
    pass
```

**CLI Error Handling**:
```python
try:
    result = service.import_tasks(path, strategy=strategy)
    typer.secho(
        f"✓ Import complete: {result.created} created, {result.updated} updated",
        fg=typer.colors.GREEN
    )
except InvalidExportFormatError as e:
    typer.secho(f"✗ Invalid file format: {e}", fg=typer.colors.RED)
except IncompatibleVersionError as e:
    typer.secho(f"✗ Incompatible format version: {e}", fg=typer.colors.RED)
except ImportError as e:
    typer.secho(f"✗ Import failed: {e}", fg=typer.colors.RED)
```

### 8. Timestamp Handling: UTC ISO 8601

**Decision**: Use UTC timestamps in ISO 8601 format for all export/import

**Rationale**:
- **Standard**: ISO 8601 is widely recognized and unambiguous
- **Timezone-aware**: UTC eliminates timezone issues
- **Pydantic support**: Automatic parsing and serialization
- **Human-readable**: Can read exported timestamps

**Format**: `2025-11-12T10:30:00Z` (with `Z` suffix for UTC)

**Implementation**:
```python
class TaskSnapshot(BaseModel):
    created_at: datetime = Field(
        ...,
        description="Creation timestamp in UTC ISO 8601 format"
    )
    updated_at: datetime = Field(
        ...,
        description="Last update timestamp in UTC ISO 8601 format"
    )

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
```

## Data Flow

### Export Workflow

```
CLI: tasky task export backup.json
  ↓
CLI.export_command(file_path="backup.json")
  ↓
TaskImportExportService.export_tasks(file_path)
  ↓ fetch all tasks
TaskService.get_all_tasks() → list[TaskModel]
  ↓ convert
TaskModel → TaskSnapshot
  ↓ create document
ExportDocument(tasks=[TaskSnapshot, ...])
  ↓ serialize
JSON file
  ↓ write
backup.json on filesystem
  ↓
CLI: "✓ Exported 42 tasks to backup.json"
```

### Import Workflow (Append)

```
CLI: tasky task import backup.json
  ↓
CLI.import_command(file_path="backup.json", strategy="append")
  ↓
TaskImportExportService.import_tasks(file_path, strategy=APPEND)
  ↓ load and validate
ExportDocument from backup.json
  ↓ convert
TaskSnapshot → TaskModel
  ↓ fetch existing
TaskService.get_all_tasks() → list[TaskModel]
  ↓ apply strategy
_apply_append_strategy(existing, imported)
  ↓ save new tasks
TaskRepository.save_task(task) × N
  ↓ return result
ImportResult(created=42, updated=0, skipped=0)
  ↓
CLI: "✓ Import complete: 42 created, 0 updated"
```

### Import Workflow (Merge)

```
CLI: tasky task import backup.json --strategy merge
  ↓
TaskImportExportService.import_tasks(file_path, strategy=MERGE)
  ↓ load and validate
ExportDocument from backup.json
  ↓ fetch existing
existing_tasks = {id → TaskModel, ...}
  ↓ for each imported task:
   ├─ if ID exists:
   │  └─ update existing task, save (result.updated++)
   └─ if ID new:
      └─ create new task, save (result.created++)
  ↓ return result
ImportResult(created=5, updated=37, skipped=0)
  ↓
CLI: "✓ Import complete: 5 created, 37 updated"
```

## Testing Strategy

### Unit Tests: Schema Validation
- Valid export documents parse successfully
- Invalid JSON rejected with clear error
- Missing required fields detected
- Version incompatibility detected
- Empty task list handled

### Unit Tests: Strategy Logic
- Append strategy creates new tasks, re-keys duplicates
- Replace strategy deletes all first, then imports
- Merge strategy updates by ID, creates if new
- Each strategy produces correct ImportResult

### Unit Tests: Timestamp Conversion
- UTC timestamps in ISO 8601 format handled correctly
- Timezone-aware datetime objects round-trip correctly
- Export timestamp is current UTC time

### Integration Tests: Export
- Export writes valid JSON to file
- Exported file contains all tasks
- Exported file can be parsed back to ExportDocument
- Round-trip preserves all task data

### Integration Tests: Import
- Import from valid file succeeds
- Import from invalid file shows helpful error
- Import with invalid version rejected
- Each strategy produces expected result

### End-to-End Tests: CLI
- `tasky task export` creates file successfully
- `tasky task import` reads file and applies strategy
- `tasky task import --dry-run` shows preview without changes
- Error messages are user-friendly
- Large imports complete in reasonable time

## Performance Considerations

- **Memory**: Load entire JSON file into memory (acceptable for <100k tasks)
- **I/O**: Single pass through file, one save per task
- **Complexity**: O(n) for append, O(n) for replace, O(n) for merge
- **Scalability**: Current approach suitable for <10k tasks; streaming needed for larger

## Security Considerations

- **Input validation**: All imported JSON validated before processing
- **Path traversal**: Use `Path.resolve()` to prevent directory traversal
- **File permissions**: Respect filesystem permissions on export file
- **Sensitive data**: No passwords or secrets in export (not applicable to current model)

## Migration Strategy

**No migration required**. This is purely additive:
1. Existing projects continue working without changes
2. Export capability available to all existing projects
3. Import capability available for any project
4. No schema changes to existing models

## Future Extensions

### 1. Incremental Export
```python
def export_tasks_since(
    self,
    since: datetime,
    file_path: Path
) -> ExportDocument:
    """Export only tasks modified since timestamp."""
    tasks = service.get_all_tasks()
    filtered = [t for t in tasks if t.updated_at >= since]
    # ... export filtered list
```

### 2. Encrypted Export
```python
def export_tasks_encrypted(
    self,
    file_path: Path,
    password: str
) -> None:
    """Export with AES encryption."""
    document = self._create_export_document()
    encrypted = encrypt_json(document.model_dump_json(), password)
    file_path.write_bytes(encrypted)
```

### 3. Streaming Import
```python
def import_tasks_stream(
    self,
    file_path: Path,
    strategy: ImportStrategy,
    chunk_size: int = 1000
) -> Iterator[ImportResult]:
    """Import large files in chunks."""
    # Stream JSON, process in batches
    yield ImportResult(...)
```

### 4. Format Conversion
```python
def export_as_csv(self, file_path: Path) -> None:
    """Export tasks as CSV."""
    # CSV header: task_id,name,details,status,created_at,updated_at
```

## Open Questions

1. Should we support importing from URLs? (Deferred to future)
2. Should we encrypt exports by default? (No, plain JSON for now)
3. Should we auto-backup before replace strategy? (Recommend manual backup)
4. Should we support partial imports (e.g., only completed tasks)? (Deferred to future filter enhancement)

## References

- VISION.md: Not explicitly mentioned but aligns with data portability goals
- Pydantic docs: https://docs.pydantic.dev/
- JSON schema best practices: https://json-schema.org/understanding-json-schema/
- ISO 8601 standard: https://en.wikipedia.org/wiki/ISO_8601
