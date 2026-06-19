from __future__ import annotations

import threading
from typing import Any, Callable

from katharos.concurrency.base_threading_backend import (
    AbstractCondition,
    AbstractLock,
    BaseThreadHandle,
    BaseThreadingBackend,
)


class ThreadingHandle(BaseThreadHandle):
    """A :class:`BaseThreadHandle` backed by a :class:`threading.Thread`."""

    def __init__(self, thread: threading.Thread) -> None:
        """Wrap an already-started thread.

        Args:
            thread: The running thread this handle refers to.
        """
        self._thread = thread

    def join(self, timeout: float | None = None) -> None:
        """Block until the underlying thread finishes (or ``timeout`` elapses).

        Args:
            timeout: Maximum seconds to wait, or ``None`` to wait forever.
        """
        self._thread.join(timeout)

    def is_alive(self) -> bool:
        """Return whether the underlying thread is still running.

        Returns:
            ``True`` while the thread is running, ``False`` once it finishes.
        """
        return self._thread.is_alive()


class ThreadingBackend(BaseThreadingBackend):
    """A threading backend built on the standard library :mod:`threading`.

    This is the default backend used by Katharos' concurrency types. Spawned
    work runs on daemon :class:`threading.Thread` instances, and the
    synchronization primitives are plain :class:`threading.Lock` and
    :class:`threading.Condition` objects.
    """

    def spawn(self, fn: Callable[[], Any]) -> ThreadingHandle:
        """Run ``fn`` on a new daemon thread.

        Args:
            fn: The zero-argument callable to run. Its return value is
                ignored.

        Returns:
            A :class:`ThreadingHandle` for the started thread.
        """
        thread = threading.Thread(target=fn, daemon=True)
        thread.start()
        return ThreadingHandle(thread)

    def create_lock(self) -> AbstractLock:
        """Create a new :class:`threading.Lock`.

        Returns:
            A standard-library lock.
        """
        return threading.Lock()

    def create_condition(self) -> AbstractCondition:
        """Create a new :class:`threading.Condition`.

        Returns:
            A standard-library condition variable.
        """
        return threading.Condition()

    def create_local(self) -> threading.local:
        """Create a new :class:`threading.local`.

        Returns:
            Standard-library thread-local storage, isolated per OS thread.
        """
        return threading.local()


_default_backend = ThreadingBackend()


def default_backend() -> ThreadingBackend:
    """Return the shared default threading backend.

    Consumers that are not given an explicit backend use this one. The
    instance is stateless and safe to share across threads.

    Returns:
        The process-wide default :class:`ThreadingBackend`.
    """
    return _default_backend
