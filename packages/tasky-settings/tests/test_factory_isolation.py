"""Tests for backend registration isolation and initialization.

These tests verify that create_task_service() works correctly without
requiring explicit tasky_storage imports, and that backend initialization
is idempotent and thread-safe.
"""

from __future__ import annotations

import subprocess
import sys
import threading
from pathlib import Path

import pytest
from tasky_settings.backend_registry import registry
from tasky_settings.factory import create_task_service
from tasky_tasks.service import TaskService


@pytest.fixture
def isolated_test_project(tmp_path: Path) -> Path:
    """Create a minimal test project for isolation testing.

    Args:
        tmp_path: pytest temporary directory

    Returns:
        Path to test project root

    """
    # Create project structure
    project_root = tmp_path / "test_project"
    tasky_dir = project_root / ".tasky"
    tasky_dir.mkdir(parents=True)

    # Create minimal config
    config_path = tasky_dir / "config.toml"
    config_path.write_text(
        """
[storage]
backend = "json"
path = "tasks.json"
""",
    )

    return project_root


def test_factory_works_without_explicit_storage_import(
    isolated_test_project: Path,
) -> None:
    """Test that create_task_service works in a subprocess without imports.

    This test runs in a subprocess to ensure true import isolation - proving that
    _ensure_backends_registered() correctly initializes backends on demand without
    requiring the caller to import tasky_storage explicitly.

    The key verification: The user code ONLY imports from tasky_settings, never
    from tasky_storage, and the factory still works.
    """
    # Create a Python script that imports ONLY from tasky_settings
    test_script = f"""
import sys
from pathlib import Path

# USER CODE: Import ONLY from tasky_settings (not tasky_storage)
from tasky_settings.factory import create_task_service
from tasky_settings.backend_registry import registry

# Verify user code did not import tasky_storage
# (It's OK if factory imported it internally - that's the fix)
import_list = [name for name in globals() if not name.startswith('_')]
assert "tasky_storage" not in import_list, "User code should not import tasky_storage"

# Create service - factory handles backend initialization internally
project_root = Path({isolated_test_project!r})
service = create_task_service(project_root=project_root)

# Verify service was created successfully
assert service is not None, "Service should be created"

# Verify backend is available (factory initialized it)
assert "json" in registry.list_backends(), "JSON backend should be registered"

# Verify the fix worked: tasky_storage was imported BY THE FACTORY, not by user code
assert "tasky_storage" in sys.modules, "Factory should have imported tasky_storage"

print("SUCCESS: Factory works without explicit tasky_storage import by user")
"""

    # Run in subprocess for true isolation
    result = subprocess.run(  # noqa: S603 -- script input is trusted (test-owned)
        [sys.executable, "-c", test_script],
        capture_output=True,
        text=True,
        check=False,
    )

    # Verify test passed
    assert result.returncode == 0, f"Subprocess test failed:\n{result.stderr}\n{result.stdout}"
    assert "SUCCESS" in result.stdout


def test_backend_initialization_is_idempotent(
    isolated_test_project: Path,
) -> None:
    """Test that calling create_task_service multiple times doesn't break.

    This verifies that _ensure_backends_registered() uses proper flag checking
    to avoid duplicate initialization attempts.
    """
    # Call factory multiple times
    _ = create_task_service(project_root=isolated_test_project)
    _ = create_task_service(project_root=isolated_test_project)
    service3 = create_task_service(project_root=isolated_test_project)

    # Service should be created successfully
    assert service3 is not None

    # Backend should still be registered
    assert "json" in registry.list_backends()


def test_backend_registry_persists_across_factory_calls(
    isolated_test_project: Path,
) -> None:
    """Test that backend registration persists across multiple factory calls.

    This ensures that the global registry state is maintained correctly.
    """
    # Create first service
    _ = create_task_service(project_root=isolated_test_project)
    backends_after_first = registry.list_backends()

    # Create second service
    _ = create_task_service(project_root=isolated_test_project)
    backends_after_second = registry.list_backends()

    # Both should have the same backends available
    assert backends_after_first == backends_after_second
    assert "json" in backends_after_second


def test_thread_safety_of_initialization(
    isolated_test_project: Path,
) -> None:
    """Test that concurrent calls to create_task_service are thread-safe.

    This verifies that the lock in _ensure_backends_registered() prevents
    race conditions when multiple threads initialize simultaneously.
    """
    errors: list[Exception] = []
    services: list[TaskService] = []

    def create_service() -> None:
        try:
            service = create_task_service(project_root=isolated_test_project)
            services.append(service)
        except Exception as e:  # noqa: BLE001
            errors.append(e)

    # Create 10 threads that all try to create services simultaneously
    threads = [threading.Thread(target=create_service) for _ in range(10)]

    # Start all threads
    for thread in threads:
        thread.start()

    # Wait for all to complete
    for thread in threads:
        thread.join()

    # Verify no errors occurred
    assert len(errors) == 0, f"Errors in threads: {errors}"

    # Verify all services were created
    assert len(services) == 10

    # Verify backend is still registered correctly
    assert "json" in registry.list_backends()
