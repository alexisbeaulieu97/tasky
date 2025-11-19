# Shared Models Specification

## ADDED Requirements

#### Requirement: Shared Task Definitions
The system MUST provide a single source of truth for task data structures shared across packages.

#### Scenario: TaskSnapshot Definition
GIVEN the `tasky-contracts` package
WHEN `TaskSnapshot` is imported
THEN it includes all standard task fields (id, name, status, etc.)
AND it is immutable (frozen)

#### Scenario: TaskStatus Definition
GIVEN the `tasky-contracts` package
WHEN `TaskStatus` is imported
THEN it provides the standard enum values (pending, completed, etc.)

## MODIFIED Requirements

#### Requirement: Task Domain Usage
The `tasky-tasks` package MUST use shared definitions for status and snapshots.

#### Scenario: TaskModel Integration
GIVEN `TaskModel` in `tasky-tasks`
WHEN a task is instantiated
THEN its `status` field uses `tasky_contracts.TaskStatus`

#### Requirement: Hook Domain Usage
The `tasky-hooks` package MUST use shared definitions for event payloads.

#### Scenario: Event Payload
GIVEN a `TaskCreatedEvent`
WHEN the event is inspected
THEN its `task_snapshot` field is of type `tasky_contracts.TaskSnapshot`
