# Refactor Shared DTOs

## Summary
Extract shared data transfer objects (DTOs) and common models into a dedicated `tasky-contracts` package to eliminate code duplication and circular dependencies between `tasky-tasks` and `tasky-hooks`.

## Problem
Currently, `TaskSnapshot` in `tasky-hooks` duplicates the structure of `TaskModel` in `tasky-tasks` to avoid circular dependencies. This violates the Single Responsibility Principle (SRP) and the Open/Closed Principle (OCP), as adding a field requires manual synchronization across packages. It also creates maintenance burden and potential for drift.

## Solution
Create a new package `packages/tasky-contracts` (or `tasky-core`) to house shared definitions. Both `tasky-tasks` and `tasky-hooks` will depend on this package.

## Impact
- **Architecture**: Introduces a new shared dependency.
- **Code Quality**: Removes duplication, enforces single source of truth.
- **Maintenance**: Simplifies adding new fields to tasks.
