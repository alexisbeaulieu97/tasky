## Task Repository

The `JsonTaskRepository` provides a high-level interface for task persistence using JSON file storage. It implements the `TaskRepository` protocol for working with `TaskModel` objects.

```python
from pathlib import Path
from tasky_storage import JsonTaskRepository
from tasky_tasks.models import TaskModel, TaskStatus

# Create repository from file path
repo = JsonTaskRepository.from_path(Path("~/tasky/tasks.json"))
repo.initialize()

# Create and save a task
task = TaskModel(name="Draft agenda", details="Prepare slides and notes")
repo.save_task(task)

# Retrieve tasks
all_tasks = repo.get_all_tasks()
specific_task = repo.get_task(task.task_id)

# Update and delete tasks
task.status = TaskStatus.COMPLETED
repo.save_task(task)
repo.delete_task(task.task_id)
```

The repository automatically manages the JSON document structure and provides type-safe operations on `TaskModel` objects. Invalid data or storage errors raise `StorageDataError`.

## Low-level JSON Storage

For advanced use cases, you can also use the lower-level `JsonStorage` class directly:

```python
from pathlib import Path
from tasky_storage import JsonStorage

store = JsonStorage(path=Path("~/tasky/custom.json"))
store.initialize({"custom": "data"})
data = store.load()
store.save(data)
```
