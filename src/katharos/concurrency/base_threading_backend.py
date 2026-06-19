from __future__ import annotations

from abc import ABC, abstractmethod
from types import TracebackType
from typing import Any, Callable, Protocol, runtime_checkable


@runtime_checkable
class AbstractLock(Protocol):
    """A mutual-exclusion lock usable as a context manager.

    Only the context-manager surface is required, which is all the
    concurrency primitives in Katharos rely on. ``threading.Lock`` satisfies
    this protocol structurally, as does any green-thread equivalent.
    """

    def __enter__(self) -> bool:
        """Acquire the lock on entering a ``with`` block."""
        ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
        /,
    ) -> bool | None:
        """Release the lock on leaving a ``with`` block."""
        ...


@runtime_checkable
class AbstractCondition(Protocol):
    """A condition variable usable as a context manager.

    Captures the subset of :class:`threading.Condition` that Katharos uses:
    acquiring the underlying lock via ``with``, waiting for a notification,
    and notifying waiters. ``threading.Condition`` satisfies this protocol
    structurally.
    """

    def __enter__(self) -> bool:
        """Acquire the underlying lock on entering a ``with`` block."""
        ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
        /,
    ) -> bool | None:
        """Release the underlying lock on leaving a ``with`` block."""
        ...

    def wait(self, timeout: float | None = None) -> bool:
        """Release the lock and block until notified (or ``timeout`` elapses).

        Args:
            timeout: Maximum seconds to wait, or ``None`` to wait forever.

        Returns:
            ``False`` if the call returned because ``timeout`` elapsed, else
            ``True``.
        """
        ...

    def notify(self, n: int = 1) -> None:
        """Wake at most ``n`` threads waiting on this condition.

        Args:
            n: The maximum number of waiters to wake.
        """
        ...

    def notify_all(self) -> None:
        """Wake all threads waiting on this condition."""
        ...


class BaseThreadHandle(ABC):
    """A handle to a unit of work started by a :class:`BaseThreadingBackend`.

    Returned by :meth:`BaseThreadingBackend.spawn`; lets callers wait for the
    spawned work to finish or check whether it is still running, without
    exposing the underlying thread implementation.
    """

    @abstractmethod
    def join(self, timeout: float | None = None) -> None:
        """Block until the spawned work finishes (or ``timeout`` elapses).

        Args:
            timeout: Maximum seconds to wait, or ``None`` to wait forever.
        """
        raise NotImplementedError()

    @abstractmethod
    def is_alive(self) -> bool:
        """Return whether the spawned work is still running.

        Returns:
            ``True`` while the work is in progress, ``False`` once it has
            finished.
        """
        raise NotImplementedError()


class BaseThreadingBackend(ABC):
    """Abstraction over a concurrency implementation.

    A backend decouples Katharos' concurrency types (such as
    :class:`~katharos.types.Lazy` and
    :class:`~katharos.concurrency.csp.Channel`) from a specific threading
    library. The default backend is built on the standard library
    :mod:`threading` module, but an alternative (for example one backed by
    ``greenlet`` or ``gevent``) can be supplied instead, as long as it
    provides compatible thread spawning and synchronization primitives.

    A backend exposes three capabilities:

    - **Spawning** lightweight units of work via :meth:`spawn`.
    - **Synchronization primitives** via :meth:`create_lock` and
      :meth:`create_condition`, so consumers coordinate using primitives that
      cooperate with the backend's scheduler.
    - **Context-local storage** via :meth:`create_local`, isolated per unit of
      concurrency the backend schedules.
    """

    @abstractmethod
    def spawn(self, fn: Callable[[], Any]) -> BaseThreadHandle:
        """Run a zero-argument callable concurrently.

        Args:
            fn: The work to run. Its return value is ignored; callers that
                need a result should arrange for ``fn`` to store it.

        Returns:
            A :class:`BaseThreadHandle` for the started work.
        """
        raise NotImplementedError()

    @abstractmethod
    def create_lock(self) -> AbstractLock:
        """Create a new mutual-exclusion lock.

        Returns:
            A lock that cooperates with this backend's scheduler.
        """
        raise NotImplementedError()

    @abstractmethod
    def create_condition(self) -> AbstractCondition:
        """Create a new condition variable.

        Returns:
            A condition variable that cooperates with this backend's
            scheduler.
        """
        raise NotImplementedError()

    @abstractmethod
    def create_local(self) -> Any:
        """Create a context-local storage object.

        The returned object stores attributes independently for each unit of
        concurrency the backend schedules: per OS thread for a thread-based
        backend, per green thread for a green-thread backend. It is used to
        hold execution-context-specific state, such as the active scopes of a
        :class:`~katharos.concurrency.csp.Go` launcher.

        Using the backend's own context-local (rather than hardcoding
        :class:`threading.local`) is what keeps that per-context state correct
        when the backend multiplexes many tasks onto a single OS thread.

        Returns:
            An object supporting arbitrary attribute get/set/delete that is
            isolated per scheduled context (for example
            :class:`threading.local`).
        """
        raise NotImplementedError()
