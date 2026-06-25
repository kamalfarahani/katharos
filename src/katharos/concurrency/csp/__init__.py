"""CSP (Communicating Sequential Processes) style concurrency for Katharos.

This module provides Go-style concurrency primitives for coordinating
concurrent computations in the CSP tradition:

    - :class:`CSP`: a runtime that binds channels and goroutines to a single
      threading backend; the :data:`csp` instance is the default runtime.
    - :class:`Go`: launch a callable concurrently, mirroring Go's ``go func()``.
    - :class:`Channel`: a Go-style, thread-safe channel for communicating
      values between threads (paired with :class:`Go`).
    - :class:`ChannelClosedError`: raised on sending to or closing a closed
      channel.
"""

from .channel import Channel, ChannelClosedError, ChannelTimeoutError
from .csp import CSP, csp
from .go import Go

__all__ = [
    "CSP",
    "Channel",
    "ChannelClosedError",
    "ChannelTimeoutError",
    "Go",
    "csp",
]
