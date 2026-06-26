"""CSP (Communicating Sequential Processes) style concurrency for Katharos.

This module provides Go-style concurrency primitives for coordinating
concurrent computations in the CSP tradition:

    - :class:`CSPRuntime`: a runtime that binds channels and goroutines to a single
      threading backend; the :data:`csp` instance is the default runtime.
    - :class:`Go`: launch a callable concurrently, mirroring Go's ``go func()``.
    - :class:`Channel`: a Go-style, thread-safe channel for communicating
      values between threads (paired with :class:`Go`).
    - :class:`ChannelClosedError`: raised on sending to or closing a closed
      channel.
    - :func:`select` / :func:`recv`: wait on whichever of several channels
      becomes ready first, mirroring Go's ``select``; :class:`SelectResult`
      describes the outcome.
"""

from .channel import Channel, ChannelClosedError, ChannelTimeoutError
from .csp import CSPRuntime, csp
from .go import Go
from .select import SelectResult, recv, select

__all__ = [
    "CSPRuntime",
    "Channel",
    "ChannelClosedError",
    "ChannelTimeoutError",
    "Go",
    "SelectResult",
    "csp",
    "recv",
    "select",
]
