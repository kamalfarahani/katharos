from __future__ import annotations

import threading
from types import TracebackType
from typing import Any, Callable

from katharos.concurrency.base_threading_backend import (
    BaseThreadHandle,
    BaseThreadingBackend,
)
from katharos.concurrency.threading_backend import default_backend


class Go:
    """Launch callables concurrently, mimicking Go's ``go func()`` statement.

    A ``Go`` instance is callable: ``go(fn, *args, **kwargs)`` runs
    ``fn(*args, **kwargs)`` concurrently on a threading backend and returns
    immediately, just like ``go f(x, y)`` starts a goroutine in Go. The work
    runs on the instance's :class:`~katharos.concurrency.BaseThreadingBackend`,
    so the concurrency model is swappable (standard threads by default, or a
    green-thread backend if supplied).

    Used as a context manager, ``Go`` becomes a *structured-concurrency
    scope*: every call made inside the ``with`` block is tracked, and leaving
    the block blocks until all of that work has finished (similar to a
    ``sync.WaitGroup``). Scopes are tracked per thread and nest correctly, so
    the module-level :data:`go` instance is safe to share. Calls made outside
    any ``with`` block are pure fire-and-forget and are not tracked.

    The module-level :data:`go` instance is bound to the default backend and
    is the one you normally use; construct your own ``Go`` only to pin a
    specific backend.

    Note:
        Like a goroutine, a callable launched here is fire-and-forget: its
        return value is discarded and an exception it raises does not
        propagate out of the scope. Use a :class:`~katharos.types.Promise` or
        a :class:`~katharos.concurrency.csp.Channel` to communicate results or
        failures back to the caller.

    Examples:
        >>> import threading
        >>> done = threading.Event()
        >>> handle = go(done.set)
        >>> handle.join()
        >>> done.is_set()
        True

        >>> results = []
        >>> handle = go(results.append, 42)
        >>> handle.join()
        >>> results
        [42]

        Used as a scope, the block waits for everything spawned inside it:

        >>> lock = threading.Lock()
        >>> collected = []
        >>> def collect(x):
        ...     with lock:
        ...         collected.append(x)
        >>> with go:
        ...     _ = go(collect, 1)
        ...     _ = go(collect, 2)
        >>> sorted(collected)
        [1, 2]
    """

    def __init__(self, backend: BaseThreadingBackend | None = None) -> None:
        """Initialize a launcher bound to a backend.

        Args:
            backend: The threading backend used to spawn work. Defaults to the
                shared
                :func:`~katharos.concurrency.threading_backend.default_backend`.
        """
        self._backend = backend or default_backend()
        self._local = threading.local()

    def _scope_stack(self) -> list[list[BaseThreadHandle]]:
        """Return the calling thread's stack of active scopes.

        Each entry is the list of handles tracked by one active ``with``
        block. The stack is thread-local, so concurrent callers never share
        scope state.

        Returns:
            The current thread's scope stack, created empty on first access.
        """
        if not hasattr(self._local, "stack"):
            self._local.stack = []
        return self._local.stack

    def __call__(
        self,
        fn: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> BaseThreadHandle:
        """Run ``fn(*args, **kwargs)`` concurrently without blocking.

        If called inside a ``with`` block on this instance, the spawned work
        is tracked and joined when the block exits.

        Args:
            fn: The callable to run concurrently. Its return value is
                discarded; use a :class:`~katharos.types.Promise` or a
                :class:`~katharos.concurrency.csp.Channel` to communicate
                results back.
            *args: Positional arguments forwarded to ``fn``.
            **kwargs: Keyword arguments forwarded to ``fn``.

        Returns:
            A :class:`~katharos.concurrency.BaseThreadHandle` for the spawned
            work, so callers can ``join`` it. It may be ignored for
            fire-and-forget use.
        """
        handle = self._backend.spawn(lambda: fn(*args, **kwargs))

        stack = self._scope_stack()
        if stack:
            stack[-1].append(handle)

        return handle

    def __enter__(self) -> Go:
        """Open a structured-concurrency scope on the calling thread.

        Returns:
            This launcher, so calls made on it inside the block are tracked.
        """
        self._scope_stack().append([])
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Close the scope, blocking until all work spawned in it finishes.

        The scope is joined even when the block exits because of an
        exception, so no spawned work outlives the block. The exception, if
        any, is allowed to propagate.

        Args:
            exc_type: The exception type if the block raised, else ``None``.
            exc_value: The exception instance if the block raised, else
                ``None``.
            traceback: The traceback if the block raised, else ``None``.
        """
        for handle in self._scope_stack().pop():
            handle.join()


go = Go()
"""The default goroutine launcher, bound to the default threading backend."""
