"""CSP (Communicating Sequential Processes) style concurrency for Katharos.

This module provides Go-style concurrency primitives for coordinating
concurrent computations in the CSP tradition:

    - :class:`CSPRuntime`: a runtime that binds channels and goroutines to a single
      threading backend; :data:`default_csp_runtime` is the shared default runtime.
    - :class:`Go`: launch a callable concurrently, mirroring Go's ``go func()``.
    - :class:`Channel`: a Go-style, thread-safe channel for communicating
      values between threads (paired with :class:`Go`).
    - :class:`ChannelClosedError`: returned as a failure by channel operations
      on closure; raised when closing an already-closed channel.
    - :func:`select` / :func:`recv`: wait on whichever of several channels
      becomes ready first, mirroring Go's ``select``; :class:`SelectResult`
      describes the outcome.
"""

from .channel import Channel, ChannelClosedError, ChannelTimeoutError
from .go import Go
from .runtime import CSPRuntime, default_csp_runtime
from .select import SelectResult, recv, select

__all__ = [
    "CSPRuntime",
    "Channel",
    "ChannelClosedError",
    "ChannelTimeoutError",
    "Go",
    "SelectResult",
    "default_csp_runtime",
    "recv",
    "select",
]
