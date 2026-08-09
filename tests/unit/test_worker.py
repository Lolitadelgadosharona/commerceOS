from apps.worker import main as worker


class FakeRedis:
    def ping(self) -> bool:
        return True


def test_worker_reaches_ready_loop(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(worker.Redis, "from_url", lambda *_args, **_kwargs: FakeRedis())
    monkeypatch.setattr(worker.signal, "signal", lambda *_args: None)

    def stop_after_first_sleep(_seconds: int) -> None:
        worker.running = False

    monkeypatch.setattr(worker.time, "sleep", stop_after_first_sleep)
    worker.running = True
    worker.main()
    assert worker.running is False
