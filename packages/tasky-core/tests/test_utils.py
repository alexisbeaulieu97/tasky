from tasky_core.task_tree import count_tasks, flatten_tasks
from tasky_models import Task


def test_flatten_tasks_preserves_hierarchy_order() -> None:
    root = Task(
        name="Parent",
        details="root",
        subtasks=[
            Task(name="Child A", details="a"),
            Task(
                name="Child B",
                details="b",
                subtasks=[
                    Task(name="Grandchild", details="c"),
                ],
            ),
        ],
    )

    flattened = list(flatten_tasks([root]))

    names = [entry.task.name for entry in flattened]
    assert names == ["Parent", "Child A", "Child B", "Grandchild"]
    child_a = flattened[1]
    assert child_a.depth == 1
    assert child_a.is_last is False
    child_b = flattened[2]
    assert child_b.depth == 1
    assert child_b.is_last is True
    grandchild = flattened[3]
    assert grandchild.depth == 2
    assert grandchild.lineage == (True, True)


def test_count_tasks_calculates_remaining_and_total() -> None:
    tree = [
        Task(
            name="Parent",
            details="root",
            completed=False,
            subtasks=[
                Task(name="Done", details="child", completed=True),
                Task(name="Pending", details="child", completed=False),
            ],
        )
    ]

    remaining, total = count_tasks(tree)

    assert total == 3
    assert remaining == 2
