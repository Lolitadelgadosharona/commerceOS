from commerce_os.growth.discovery_services import (
    RESEARCH_OUTPUT_SCHEMA,
    WEB_DISCOVERY_OUTPUT_SCHEMA,
)

from apps.worker import main as worker


class FakeRedis:
    def ping(self) -> bool:
        return True

    def set(self, _key: str, _value: str, *, ex: int) -> bool:
        return ex > 0


def _assert_strict_object_schemas(schema: dict[str, object]) -> None:
    if schema.get("type") == "object":
        assert schema.get("additionalProperties") is False
        properties = schema.get("properties")
        assert isinstance(properties, dict)
        required = schema.get("required")
        assert isinstance(required, list)
        assert set(required) == set(properties)
        for value in properties.values():
            assert isinstance(value, dict)
            _assert_strict_object_schemas(value)
    if schema.get("type") == "array":
        items = schema.get("items")
        assert isinstance(items, dict)
        _assert_strict_object_schemas(items)


def test_growth_research_schema_is_strict_provider_compatible() -> None:
    _assert_strict_object_schemas(RESEARCH_OUTPUT_SCHEMA)
    _assert_strict_object_schemas(WEB_DISCOVERY_OUTPUT_SCHEMA)
    assert WEB_DISCOVERY_OUTPUT_SCHEMA["properties"]["candidates"]["maxItems"] == 10  # type: ignore[index]


def test_worker_reaches_ready_loop(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(worker.Redis, "from_url", lambda *_args, **_kwargs: FakeRedis())
    monkeypatch.setattr(worker.signal, "signal", lambda *_args: None)

    def stop_after_first_sleep(_seconds: int) -> None:
        worker.running = False

    monkeypatch.setattr(worker.time, "sleep", stop_after_first_sleep)
    worker.running = True
    worker.main()
    assert worker.running is False
