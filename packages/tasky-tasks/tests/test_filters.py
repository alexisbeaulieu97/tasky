"""Unit tests for TaskFilter model and filtering logic."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from tasky_tasks.models import TaskFilter, TaskModel, TaskStatus


@pytest.fixture
def sample_task() -> TaskModel:
    """Create a sample task for testing."""
    return TaskModel(
        task_id=uuid4(),
        name="Fix bug in authentication",
        details="Users cannot log in with special characters",
        status=TaskStatus.PENDING,
        created_at=datetime(2025, 11, 10, 12, 0, 0, tzinfo=UTC),
        updated_at=datetime(2025, 11, 10, 12, 0, 0, tzinfo=UTC),
    )


class TestTaskFilterStatusFiltering:
    """Test status filtering with TaskFilter."""

    def test_matches_single_status(self, sample_task: TaskModel) -> None:
        """Test that filter matches task with specified status."""
        task_filter = TaskFilter(statuses=[TaskStatus.PENDING])
        assert task_filter.matches(sample_task)

    def test_rejects_different_status(self, sample_task: TaskModel) -> None:
        """Test that filter rejects task with different status."""
        task_filter = TaskFilter(statuses=[TaskStatus.COMPLETED])
        assert not task_filter.matches(sample_task)

    def test_matches_multiple_statuses(self, sample_task: TaskModel) -> None:
        """Test that filter matches task when status is in list."""
        task_filter = TaskFilter(
            statuses=[TaskStatus.PENDING, TaskStatus.COMPLETED],
        )
        assert task_filter.matches(sample_task)

    def test_no_status_filter_matches_all(self, sample_task: TaskModel) -> None:
        """Test that None status filter matches any task."""
        task_filter = TaskFilter(statuses=None)
        assert task_filter.matches(sample_task)


class TestTaskFilterDateRangeFiltering:
    """Test date range filtering with TaskFilter."""

    def test_created_after_inclusive(self, sample_task: TaskModel) -> None:
        """Test that created_after filter is inclusive."""
        # Task created at 2025-11-10 12:00:00
        task_filter = TaskFilter(
            created_after=datetime(2025, 11, 10, 12, 0, 0, tzinfo=UTC),
        )
        assert task_filter.matches(sample_task)

    def test_created_after_rejects_earlier(self, sample_task: TaskModel) -> None:
        """Test that created_after rejects tasks created before the date."""
        task_filter = TaskFilter(
            created_after=datetime(2025, 11, 11, 0, 0, 0, tzinfo=UTC),
        )
        assert not task_filter.matches(sample_task)

    def test_created_before_exclusive(self, sample_task: TaskModel) -> None:
        """Test that created_before filter is exclusive."""
        # Task created at 2025-11-10 12:00:00
        task_filter = TaskFilter(
            created_before=datetime(2025, 11, 10, 12, 0, 0, tzinfo=UTC),
        )
        assert not task_filter.matches(sample_task)

    def test_created_before_accepts_earlier(self, sample_task: TaskModel) -> None:
        """Test that created_before accepts tasks created before the date."""
        task_filter = TaskFilter(
            created_before=datetime(2025, 11, 11, 0, 0, 0, tzinfo=UTC),
        )
        assert task_filter.matches(sample_task)

    def test_date_range_both_boundaries(self, sample_task: TaskModel) -> None:
        """Test filtering with both created_after and created_before."""
        # Task created at 2025-11-10 12:00:00
        task_filter = TaskFilter(
            created_after=datetime(2025, 11, 10, 0, 0, 0, tzinfo=UTC),
            created_before=datetime(2025, 11, 11, 0, 0, 0, tzinfo=UTC),
        )
        assert task_filter.matches(sample_task)

    def test_date_range_excludes_outside_range(
        self,
        sample_task: TaskModel,
    ) -> None:
        """Test that tasks outside date range are excluded."""
        # Task created at 2025-11-10 12:00:00
        task_filter = TaskFilter(
            created_after=datetime(2025, 11, 11, 0, 0, 0, tzinfo=UTC),
            created_before=datetime(2025, 11, 12, 0, 0, 0, tzinfo=UTC),
        )
        assert not task_filter.matches(sample_task)

    def test_no_date_filter_matches_all(self, sample_task: TaskModel) -> None:
        """Test that None date filters match any task."""
        task_filter = TaskFilter(created_after=None, created_before=None)
        assert task_filter.matches(sample_task)


class TestTaskFilterTextSearch:
    """Test text search filtering with TaskFilter."""

    def test_search_matches_name(self, sample_task: TaskModel) -> None:
        """Test that search matches text in task name."""
        task_filter = TaskFilter(name_contains="bug")
        assert task_filter.matches(sample_task)

    def test_search_matches_details(self, sample_task: TaskModel) -> None:
        """Test that search matches text in task details."""
        task_filter = TaskFilter(name_contains="log in")
        assert task_filter.matches(sample_task)

    def test_search_case_insensitive(self, sample_task: TaskModel) -> None:
        """Test that search is case-insensitive."""
        task_filter = TaskFilter(name_contains="BUG")
        assert task_filter.matches(sample_task)

        task_filter = TaskFilter(name_contains="AUTHENTICATION")
        assert task_filter.matches(sample_task)

    def test_search_rejects_non_matching_text(
        self,
        sample_task: TaskModel,
    ) -> None:
        """Test that search rejects tasks without matching text."""
        task_filter = TaskFilter(name_contains="database")
        assert not task_filter.matches(sample_task)

    def test_search_partial_match(self, sample_task: TaskModel) -> None:
        """Test that search matches partial words."""
        task_filter = TaskFilter(name_contains="auth")
        assert task_filter.matches(sample_task)

    def test_no_search_filter_matches_all(self, sample_task: TaskModel) -> None:
        """Test that None search filter matches any task."""
        task_filter = TaskFilter(name_contains=None)
        assert task_filter.matches(sample_task)


class TestTaskFilterCombinedCriteria:
    """Test combining multiple filter criteria with AND logic."""

    def test_status_and_date_both_match(self, sample_task: TaskModel) -> None:
        """Test that task matches when both status and date criteria match."""
        task_filter = TaskFilter(
            statuses=[TaskStatus.PENDING],
            created_after=datetime(2025, 11, 10, 0, 0, 0, tzinfo=UTC),
        )
        assert task_filter.matches(sample_task)

    def test_status_matches_but_date_fails(
        self,
        sample_task: TaskModel,
    ) -> None:
        """Test that task is rejected when status matches but date doesn't."""
        task_filter = TaskFilter(
            statuses=[TaskStatus.PENDING],
            created_after=datetime(2025, 11, 11, 0, 0, 0, tzinfo=UTC),
        )
        assert not task_filter.matches(sample_task)

    def test_date_matches_but_status_fails(
        self,
        sample_task: TaskModel,
    ) -> None:
        """Test that task is rejected when date matches but status doesn't."""
        task_filter = TaskFilter(
            statuses=[TaskStatus.COMPLETED],
            created_after=datetime(2025, 11, 10, 0, 0, 0, tzinfo=UTC),
        )
        assert not task_filter.matches(sample_task)

    def test_status_and_search_both_match(self, sample_task: TaskModel) -> None:
        """Test that task matches when both status and search match."""
        task_filter = TaskFilter(
            statuses=[TaskStatus.PENDING],
            name_contains="authentication",
        )
        assert task_filter.matches(sample_task)

    def test_date_and_search_both_match(self, sample_task: TaskModel) -> None:
        """Test that task matches when both date and search match."""
        task_filter = TaskFilter(
            created_after=datetime(2025, 11, 10, 0, 0, 0, tzinfo=UTC),
            name_contains="bug",
        )
        assert task_filter.matches(sample_task)

    def test_all_criteria_match(self, sample_task: TaskModel) -> None:
        """Test that task matches when all criteria match."""
        task_filter = TaskFilter(
            statuses=[TaskStatus.PENDING],
            created_after=datetime(2025, 11, 10, 0, 0, 0, tzinfo=UTC),
            created_before=datetime(2025, 11, 11, 0, 0, 0, tzinfo=UTC),
            name_contains="authentication",
        )
        assert task_filter.matches(sample_task)

    def test_one_criterion_fails_rejects_task(
        self,
        sample_task: TaskModel,
    ) -> None:
        """Test that task is rejected if any criterion fails."""
        # All match except search
        task_filter = TaskFilter(
            statuses=[TaskStatus.PENDING],
            created_after=datetime(2025, 11, 10, 0, 0, 0, tzinfo=UTC),
            created_before=datetime(2025, 11, 11, 0, 0, 0, tzinfo=UTC),
            name_contains="database",
        )
        assert not task_filter.matches(sample_task)


class TestTaskFilterEdgeCases:
    """Test edge cases in TaskFilter behavior."""

    def test_empty_filter_matches_all(self, sample_task: TaskModel) -> None:
        """Test that filter with all None values matches any task."""
        task_filter = TaskFilter(
            statuses=None,
            created_after=None,
            created_before=None,
            name_contains=None,
        )
        assert task_filter.matches(sample_task)

    def test_empty_status_list_behavior(self, sample_task: TaskModel) -> None:
        """Test behavior with empty status list."""
        task_filter = TaskFilter(statuses=[])
        # Empty list means no status will match
        assert not task_filter.matches(sample_task)

    def test_whitespace_search_text(self, sample_task: TaskModel) -> None:
        """Test search with whitespace in query."""
        task_filter = TaskFilter(name_contains="Fix bug")
        assert task_filter.matches(sample_task)

    def test_empty_string_search(self, sample_task: TaskModel) -> None:
        """Test that empty string search matches all tasks."""
        task_filter = TaskFilter(name_contains="")
        assert task_filter.matches(sample_task)
