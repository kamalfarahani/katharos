import threading
from typing import Any, Callable

from katharos.concurrency import (
    AbstractCondition,
    AbstractLock,
    BaseThreadHandle,
    BaseThreadingBackend,
    Channel,
    ThreadingBackend,
    ThreadingHandle,
    default_backend,
)


class TestThreadingBackend:
    def test_spawn_returns_thread_handle(self):
        backend = ThreadingBackend()

        handle = backend.spawn(lambda: None)
        handle.join()

        assert isinstance(handle, BaseThreadHandle)
        assert isinstance(handle, ThreadingHandle)

    def test_spawn_runs_callable(self):
        backend = ThreadingBackend()
        ran = threading.Event()

        handle = backend.spawn(ran.set)
        handle.join()

        assert ran.is_set()

    def test_spawn_uses_daemon_thread(self):
        backend = ThreadingBackend()
        release = threading.Event()
        seen: list[bool] = []

        def work():
            seen.append(threading.current_thread().daemon)
            release.wait()

        handle = backend.spawn(work)
        release.set()
        handle.join()

        assert seen == [True]

    def test_is_alive_reflects_running_state(self):
        backend = ThreadingBackend()
        release = threading.Event()

        handle = backend.spawn(release.wait)
        assert handle.is_alive()

        release.set()
        handle.join()
        assert not handle.is_alive()

    def test_create_lock_satisfies_protocol(self):
        backend = ThreadingBackend()

        lock = backend.create_lock()

        assert isinstance(lock, AbstractLock)
        with lock:
            pass

    def test_create_condition_satisfies_protocol(self):
        backend = ThreadingBackend()

        cond = backend.create_condition()

        assert isinstance(cond, AbstractCondition)
        with cond:
            cond.notify_all()

    def test_create_local_stores_attributes(self):
        backend = ThreadingBackend()

        local = backend.create_local()
        local.value = 42

        assert local.value == 42

    def test_create_local_is_isolated_per_thread(self):
        backend = ThreadingBackend()
        local = backend.create_local()
        local.value = "main"
        seen: list[bool] = []

        def worker():
            # The attribute set on the main thread is not visible here.
            seen.append(hasattr(local, "value"))

        thread = threading.Thread(target=worker)
        thread.start()
        thread.join()

        assert seen == [False]
        assert local.value == "main"


class TestDefaultBackend:
    def test_default_backend_is_threading_backend(self):
        assert isinstance(default_backend(), ThreadingBackend)

    def test_default_backend_is_shared(self):
        assert default_backend() is default_backend()


class RecordingBackend(BaseThreadingBackend):
    """A backend that delegates to threading while recording every call."""

    def __init__(self) -> None:
        self.spawned: list[Callable[[], Any]] = []
        self.locks_created = 0
        self.conditions_created = 0
        self._delegate = ThreadingBackend()

    def spawn(self, fn: Callable[[], Any]) -> BaseThreadHandle:
        self.spawned.append(fn)
        return self._delegate.spawn(fn)

    def create_lock(self) -> AbstractLock:
        self.locks_created += 1
        return self._delegate.create_lock()

    def create_condition(self) -> AbstractCondition:
        self.conditions_created += 1
        return self._delegate.create_condition()

    def create_local(self) -> Any:
        return self._delegate.create_local()


class TestBackendInjection:
    def test_channel_uses_injected_backend_condition(self):
        backend = RecordingBackend()

        Channel[int](backend=backend)

        assert backend.conditions_created == 1
