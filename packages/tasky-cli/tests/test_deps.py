from __future__ import annotations
from pathlib import Path

from tasky_cli import deps
from tasky_settings import ProjectSettingsService


class DummyService:
    def __init__(self, path: Path | None) -> None:
        self.path = path


class DummyProjectQueryService:
    pass


class DummySettingsService:
    pass


class RecordingSettingsService(ProjectSettingsService):
    def __init__(self) -> None:
        super().__init__()
        self.requests: list[Path | None] = []

    def build_task_service(self, project_path: Path | None = None):
        self.requests.append(project_path)
        return DummyService(project_path)


def teardown_module(module):
    deps.reset_dependencies()


def test_configure_dependencies_overrides_task_service_factory(tmp_path: Path) -> None:
    captured: list[Path | None] = []

    def factory(project_path: Path | None = None) -> DummyService:
        captured.append(project_path)
        return DummyService(project_path)

    deps.configure_dependencies(task_service_factory=factory)
    try:
        service = deps.get_task_service(tmp_path)
        assert isinstance(service, DummyService)
        assert captured == [tmp_path]
    finally:
        deps.reset_dependencies()


def test_configure_dependencies_overrides_project_query_service() -> None:
    instance = DummyProjectQueryService()

    def factory() -> DummyProjectQueryService:
        return instance

    deps.configure_dependencies(project_query_service_factory=factory)
    try:
        service = deps.get_project_query_service()
        assert service is instance
    finally:
        deps.reset_dependencies()


def test_configure_dependencies_overrides_settings_service() -> None:
    instance = DummySettingsService()

    def factory() -> DummySettingsService:
        return instance

    deps.configure_dependencies(settings_service_factory=factory)
    service = deps.get_settings_service()
    assert service is instance


def test_settings_factory_override_shared_between_services(tmp_path: Path) -> None:
    recording = RecordingSettingsService()
    deps.configure_dependencies(settings_service_factory=lambda: recording)

    task_service = deps.get_task_service(tmp_path)
    query_service = deps.get_project_query_service()

    assert isinstance(task_service, DummyService)
    assert recording.requests == [tmp_path]
    assert query_service._settings is recording  # type: ignore[attr-defined]
    assert deps.get_settings_service() is recording


def test_default_settings_service_is_singleton() -> None:
    deps.reset_dependencies()
    first = deps.get_settings_service()
    second = deps.get_settings_service()
    assert first is second
