"""CSP (Communicating Sequential Processes) style concurrency for Katharos.

This module provides Go-style concurrency primitives for coordinating
concurrent computations in the CSP tradition:

    - :func:`go`: launch a callable concurrently, mirroring Go's ``go func()``.
    - :class:`Channel`: a Go-style, thread-safe channel for communicating
      values between threads (paired with :func:`go`).
    - :class:`ChannelClosedError`: raised on sending to or closing a closed
      channel.
"""

from .channel import Channel, ChannelClosedError, ChannelTimeoutError
from .go import Go, go

__all__ = [
    "Channel",
    "ChannelClosedError",
    "ChannelTimeoutError",
    "Go",
    "go",
]
