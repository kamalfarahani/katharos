"""Concurrency backends and primitives for Katharos.

A :class:`BaseThreadingBackend` abstracts thread spawning and synchronization
primitives so concurrency types (such as :class:`~katharos.types.Lazy` and
:class:`~katharos.concurrency.csp.Channel`) are not tied to a specific
threading library. :class:`ThreadingBackend` is the standard-library default.
"""

from .base_threading_backend import (
    AbstractCondition,
    AbstractLock,
    BaseThreadHandle,
    BaseThreadingBackend,
)
from .csp import CSP, Channel, ChannelClosedError, ChannelTimeoutError, Go, csp, go
from .threading_backend import ThreadingBackend, ThreadingHandle, default_backend

__all__ = [
    "AbstractCondition",
    "AbstractLock",
    "BaseThreadHandle",
    "BaseThreadingBackend",
    "CSP",
    "Channel",
    "ChannelClosedError",
    "ChannelTimeoutError",
    "Go",
    "ThreadingBackend",
    "ThreadingHandle",
    "default_backend",
    "go",
    "csp",
]
