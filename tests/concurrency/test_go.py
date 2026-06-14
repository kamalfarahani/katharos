import threading
import time
from typing import Any, Callable

import pytest

from katharos.concurrency import (
    AbstractCondition,
    AbstractLock,
    BaseThreadHandle,
    BaseThreadingBackend,
    Go,
    go,
)
from katharos.concurrency.threading_backend import ThreadingBackend, default_backend


class RecordingBackend(BaseThreadingBackend):
    """A backend that delegates to threading while recording spawned work."""

    def __init__(self) -> None:
        self.spawned: list[Callable[[], Any]] = []
        self._delegate = ThreadingBackend()

    def spawn(self, fn: Callable[[], Any]) -> BaseThreadHandle:
        self.spawned.append(fn)
        return self._delegate.spawn(fn)

    def create_lock(self) -> AbstractLock:
        return self._delegate.create_lock()

    def create_condition(self) -> AbstractCondition:
        return self._delegate.create_condition()

    def create_local(self) -> Any:
        return self._delegate.create_local()


class TestGo:
    def test_runs_callable_concurrently(self):
        ran = threading.Event()

        handle = go(ran.set)
        handle.join()

        assert ran.is_set()

    def test_returns_thread_handle(self):
        handle = go(lambda: None)
        handle.join()

        assert isinstance(handle, BaseThreadHandle)

    def test_forwards_positional_args(self):
        results: list[int] = []

        handle = go(results.append, 42)
        handle.join()

        assert results == [42]

    def test_forwards_keyword_args(self):
        captured: dict[str, Any] = {}

        def record(*, value: int) -> None:
            captured["value"] = value

        handle = go(record, value=7)
        handle.join()

        assert captured == {"value": 7}

    def test_does_not_block_caller(self):
        release = threading.Event()

        handle = go(release.wait)

        assert handle.is_alive()
        release.set()
        handle.join()
        assert not handle.is_alive()


class TestGoScope:
    def test_scope_joins_spawned_work(self):
        lock = threading.Lock()
        collected: list[int] = []

        def collect(x: int) -> None:
            with lock:
                collected.append(x)

        with go:
            go(collect, 1)
            go(collect, 2)

        # On block exit, both tasks have already been joined.
        assert sorted(collected) == [1, 2]

    def test_scope_waits_for_slow_work(self):
        finished = threading.Event()

        with go:
            go(lambda: (time.sleep(0.02), finished.set()))

        assert finished.is_set()

    def test_calls_outside_scope_are_not_tracked(self):
        launch = Go()
        handle = launch(lambda: None)
        handle.join()

        assert launch._scope_stack() == []

    def test_scopes_nest(self):
        lock = threading.Lock()
        order: list[str] = []

        def record(tag: str) -> None:
            with lock:
                order.append(tag)

        with go:
            go(record, "outer")
            with go:
                go(record, "inner")
            # Inner scope has been joined; "inner" is recorded by now.
            assert "inner" in order

        assert sorted(order) == ["inner", "outer"]

    def test_scope_joins_even_when_body_raises(self):
        done = threading.Event()

        with pytest.raises(ValueError, match="boom"):
            with go:
                go(lambda: (time.sleep(0.01), done.set()))
                raise ValueError("boom")

        assert done.is_set()


class TestGoScopeThreadIsolation:
    """Confirm the behavior that ``Go._local`` (thread-local storage) provides.

    Each of these would fail (or deadlock) if scope state were a single
    shared list on the ``go`` singleton instead of per-thread storage.
    """

    def test_concurrent_scopes_do_not_interfere(self):
        a_in_scope = threading.Event()
        a_release = threading.Event()
        a_task_done = threading.Event()
        b_done = threading.Event()

        def thread_a():
            def slow():
                a_release.wait()
                a_task_done.set()

            with go:
                go(slow)
                a_in_scope.set()
            # A's __exit__ joins `slow`, so this thread blocks until release.

        def thread_b():
            a_in_scope.wait()  # A is inside its scope with a task pending.
            with go:
                go(lambda: None)
            b_done.set()

        ta = threading.Thread(target=thread_a)
        tb = threading.Thread(target=thread_b)
        ta.start()
        tb.start()

        # B's scope must close without waiting for A's still-blocked task.
        # With a shared scope list, B would join A's `slow` task and hang here.
        assert b_done.wait(timeout=2.0)
        assert not a_task_done.is_set()

        a_release.set()
        ta.join(timeout=2.0)
        tb.join(timeout=2.0)
        assert a_task_done.is_set()
        assert not ta.is_alive()
        assert not tb.is_alive()

    def test_each_scope_joins_only_its_own_tasks(self):
        n_threads = 16
        tasks_per_thread = 5
        errors: list[BaseException] = []
        completed: list[int] = []
        results_lock = threading.Lock()

        def worker(tid: int):
            try:
                done: list[tuple[int, int]] = []
                done_lock = threading.Lock()

                with go:
                    for i in range(tasks_per_thread):

                        def task(i: int = i) -> None:
                            # A small delay so that, if the scope fails to
                            # join this thread's own tasks, `done` is still
                            # incomplete when the block exits.
                            time.sleep(0.02)
                            with done_lock:
                                done.append((tid, i))

                        go(task)

                # On block exit every task this thread spawned has run,
                # and no other thread's tasks leaked into this scope.
                assert len(done) == tasks_per_thread
                assert all(t == tid for t, _ in done)
            except BaseException as exc:  # noqa: BLE001
                with results_lock:
                    errors.append(exc)
            else:
                with results_lock:
                    completed.append(tid)

        threads = [
            threading.Thread(target=worker, args=(tid,)) for tid in range(n_threads)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=5.0)

        assert errors == []
        assert sorted(completed) == list(range(n_threads))

    def test_scope_does_not_capture_calls_from_other_threads(self):
        in_scope = threading.Event()
        spawned = threading.Event()
        release = threading.Event()

        def other():
            in_scope.wait()
            go(release.wait)  # runs on another thread; must not enter main's scope
            spawned.set()

        helper = threading.Thread(target=other)
        helper.start()

        with go:
            in_scope.set()
            spawned.wait()
            # The other thread's call landed in its own (empty) thread-local
            # stack, not the scope open on this thread.
            assert go._scope_stack()[-1] == []
            release.set()

        helper.join(timeout=2.0)
        assert not helper.is_alive()


class TestGoBackend:
    def test_default_go_uses_default_backend(self):
        assert go._backend is default_backend()

    def test_uses_injected_backend(self):
        backend = RecordingBackend()
        launch = Go(backend=backend)
        ran = threading.Event()

        handle = launch(ran.set)
        handle.join()

        assert len(backend.spawned) == 1
        assert ran.is_set()
