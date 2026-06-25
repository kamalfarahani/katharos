from __future__ import annotations

from katharos.concurrency.base_threading_backend import BaseThreadingBackend
from katharos.concurrency.threading_backend import default_backend

from .channel import Channel
from .go import Go


class CSPRuntime:
    """A CSP runtime that binds channels and goroutines to one backend.

    ``CSPRuntime`` bundles Katharos' Communicating Sequential Processes primitives --
    :class:`~katharos.concurrency.csp.Channel` and
    :class:`~katharos.concurrency.csp.Go` -- around a single
    :class:`~katharos.concurrency.BaseThreadingBackend`. Channels created via
    :attr:`Channel` and work launched via :attr:`go` all run on (and
    synchronize through) that one backend, so the whole concurrency model is
    swappable in a single place.

    The two members are:

    - :attr:`Channel`: a backend-bound channel class. Subscript it with the
      element type and call it to construct a channel:
      ``ch = csp.Channel[int](capacity=1)``. The ``backend`` is supplied
      automatically, so callers never pass it.
    - :attr:`go`: a backend-bound :class:`~katharos.concurrency.csp.Go`
      launcher. Call it to run work concurrently (``csp.go(fn, *args)``) or use
      it as a ``with`` block for structured concurrency.

    Examples:
        >>> from katharos.concurrency.threading_backend import ThreadingBackend
        >>> csp = CSPRuntime(ThreadingBackend())
        >>> ch = csp.Channel[int](capacity=1)
        >>> _ = csp.go(ch.send, 42)
        >>> ch.recv()
        Success(42)

        Used as a structured-concurrency scope, the block waits for everything
        launched inside it:

        >>> ch = csp.Channel[int]()
        >>> with csp.go:
        ...     _ = csp.go(ch.send, 1)
        ...     received = ch.recv()
        >>> received
        Success(1)
    """

    def __init__(self, backend: BaseThreadingBackend | None = None) -> None:
        """Initialize a CSP runtime bound to a backend.

        Args:
            backend: The threading backend that channels and goroutines from
                this runtime use. Defaults to the shared
                :func:`~katharos.concurrency.threading_backend.default_backend`.
        """
        self._backend = backend or default_backend()
        self.go = Go(self._backend)

        _backend = self._backend

        class BoundChannel[A](Channel[A]):
            """A :class:`Channel` pre-bound to this runtime's backend."""

            def __init__(self, capacity: int = 0) -> None:
                super().__init__(capacity, backend=_backend)

        self.Channel = BoundChannel

    @property
    def backend(self) -> BaseThreadingBackend:
        """The threading backend shared by this runtime's channels and goroutines."""
        return self._backend


csp = CSPRuntime()
"""The default CSP runtime, bound to the default threading backend."""
