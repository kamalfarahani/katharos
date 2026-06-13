"""Concurrency primitives for Katharos.

This module provides tools for coordinating concurrent computations:

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
