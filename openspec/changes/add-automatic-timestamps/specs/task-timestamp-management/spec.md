# Specification Delta: Task Timestamp Management

**Change ID**: `add-automatic-timestamps`  
**Capability**: `task-timestamp-management`  
**Type**: New Capability

---

## ADDED Requirements

### Requirement: Tasks must track creation time in UTC

The `TaskModel` SHALL automatically set the `created_at` field to the current UTC timestamp when a task is created. The timestamp MUST be timezone-aware (include `tzinfo` set to UTC) to eliminate ambiguity across different timezones and provide a clear audit trail of when tasks were created.

#### Scenario: Creating a new task sets UTC timestamp

- **WHEN** a user creates a task with name "Write documentation" and details "Update README"
- **THEN** the task's `created_at` field is set to the current UTC timestamp
- **AND** the timestamp is timezone-aware (has `tzinfo` set to UTC)

---

### Requirement: Tasks must track last modification time in UTC

The `TaskModel` SHALL automatically set the `updated_at` field to the current UTC timestamp when a task is created or modified. This enables users to see when tasks were last modified, supporting workflow tracking and debugging.

#### Scenario: Creating a new task sets both timestamps

- **WHEN** a user creates a task
- **THEN** both `created_at` and `updated_at` are set to the current UTC timestamp
- **AND** both timestamps are equal at creation time

#### Scenario: Updating a task refreshes the update timestamp

- **GIVEN** a task that was created 5 minutes ago
- **WHEN** the task is updated through `TaskService.update_task()`
- **THEN** the task's `updated_at` timestamp is set to the current UTC time
- **AND** the `created_at` timestamp remains unchanged
- **AND** `updated_at` is greater than `created_at`

---

### Requirement: TaskModel must provide explicit method to mark updates

The `TaskModel` SHALL provide a `mark_updated()` method that explicitly sets the `updated_at` timestamp to the current UTC time. This makes timestamp updates visible in code rather than relying on implicit validators, improving testability and code clarity.

#### Scenario: Calling mark_updated refreshes timestamp

- **GIVEN** a task with an existing `updated_at` timestamp
- **WHEN** the `mark_updated()` method is called
- **THEN** the `updated_at` field is set to the current UTC time
- **AND** the new timestamp is later than the previous timestamp

#### Scenario: mark_updated preserves creation timestamp

- **GIVEN** a task with `created_at` set to a specific time
- **WHEN** `mark_updated()` is called multiple times
- **THEN** the `created_at` timestamp never changes
- **AND** only `updated_at` is modified

---

### Requirement: TaskService must automatically update timestamps on modification

The `TaskService` SHALL call `task.mark_updated()` before saving any task modification to ensure consistency. All task modifications through the service layer MUST automatically track update time.

#### Scenario: Service update_task calls mark_updated

- **GIVEN** a task retrieved from the repository
- **WHEN** `TaskService.update_task(task)` is called
- **THEN** the service calls `task.mark_updated()` before saving
- **AND** the repository stores the task with the new timestamp

---

### Requirement: Timestamps must be serializable and persistable

The task timestamps SHALL be serializable to JSON and persistable in storage backends while preserving timezone information. This ensures timestamps can be saved to storage and loaded back without losing timezone information.

#### Scenario: Timezone-aware datetimes serialize to JSON

- **GIVEN** a task with UTC timestamps
- **WHEN** the task is serialized using `model_dump()` or `model_dump_json()`
- **THEN** the timestamps are included in the output
- **AND** the timezone information is preserved in ISO 8601 format

#### Scenario: Loading task from storage preserves timestamps

- **GIVEN** a task stored with UTC timestamps
- **WHEN** the task is loaded from the repository
- **THEN** the `created_at` and `updated_at` fields are timezone-aware
- **AND** the `tzinfo` is set to UTC
- **AND** the timestamp values match the stored values

---

## Test Coverage Requirements

- Unit tests for `TaskModel.mark_updated()` behavior
- Unit tests for UTC timezone enforcement
- Integration tests for `TaskService.update_task()` timestamp handling
- Serialization/deserialization tests for datetime fields
- Test that `created_at` is immutable after creation
- Test that `updated_at` changes on each modification

---

## Documentation Requirements

- Add docstring to `mark_updated()` method explaining its purpose
- Update `TaskModel` docstring to mention automatic UTC timestamps
- Document in code comments that timestamps are timezone-aware

---

## Acceptance Criteria

✅ All task instances have `created_at` set to UTC time on creation  
✅ All task instances have `updated_at` set to UTC time on creation  
✅ `TaskModel.mark_updated()` method exists and updates `updated_at`  
✅ `TaskService.update_task()` calls `mark_updated()` before saving  
✅ Timestamps preserve timezone information through serialization  
✅ All tests pass (`uv run pytest`)  
✅ Code passes linting (`uv run ruff check`)
