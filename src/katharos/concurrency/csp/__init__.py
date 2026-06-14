"""CSP (Communicating Sequential Processes) style concurrency for Katharos.

This module provides Go-style channels (paired with :meth:`katharos.types.Promise.go`)
for coordinating concurrent computations in the CSP tradition:

    - :class:`Channel`: a Go-style, thread-safe channel for communicating
      values between threads (paired with :meth:`katharos.types.Promise.go`).
    - :class:`ChannelClosedError`: raised on sending to or closing a closed
      channel.
"""

from .channel import Channel, ChannelClosedError

__all__ = [
    "Channel",
    "ChannelClosedError",
]
