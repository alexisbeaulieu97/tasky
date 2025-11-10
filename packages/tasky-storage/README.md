## JSON Document Store

The `JsonDocumentStore` persists a single JSON-compatible document to disk. Instantiate it with a path, call `load()` to retrieve the current document, and `save()` to overwrite it.

```python
from pathlib import Path
from tasky_storage import JsonDocumentStore

store = JsonDocumentStore(Path("~/tasky/storage.json"))
document = store.load()
document.setdefault("tasks", []).append({"id": "task-1", "title": "Draft agenda"})
store.save(document)
```

Files are created on demand and always stored as a JSON object. Invalid payloads or non-serialisable data raise `StorageDataError`.
