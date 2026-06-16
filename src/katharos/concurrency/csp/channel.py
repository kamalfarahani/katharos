from __future__ import annotations

import time
from collections import deque
from collections.abc import Iterator

from katharos.concurrency.base_threading_backend import BaseThreadingBackend
from katharos.concurrency.threading_backend import default_backend
from katharos.types.result import Result


class ChannelClosedError(Exception):
    """Raised when sending on, or closing, an already-closed channel."""


class ChannelTimeoutError(Exception):
    """Raised when a channel operation times out."""


class _Slot[A]:
    """A single value in transit through a channel.

    Wrapping each value gives an unbuffered :meth:`Channel.send` a stable
    identity to wait on: the sender blocks until *its own* slot is marked
    ``taken`` by a receiver, rather than inferring delivery from the shared
    buffer being empty (which is unsafe when senders contend).
    """

    __slots__ = ("value", "taken")

    def __init__(self, value: A) -> None:
        self.value = value
        self.taken = False


class Channel[A]:
    """A Go-style channel for communicating values between threads.

    A ``Channel`` is a typed, thread-safe conduit. Producers :meth:`send`
    values and consumers :meth:`recv` them; both operations block to
    coordinate the two sides, mirroring Go's channels.

    The ``capacity`` controls buffering:

    - **Unbuffered** (``capacity == 0``, the default): every :meth:`send`
      blocks until another thread is ready to :meth:`recv` the value, giving
      a synchronous hand-off (rendezvous).
    - **Buffered** (``capacity > 0``): :meth:`send` only blocks once the
      buffer is full, and :meth:`recv` only blocks once it is empty.

    Unlike Go, :meth:`recv` returns a :class:`~katharos.types.Result`:
    ``Success(value)`` while values are available, ``Failure(ChannelClosedError)``
    once the channel is closed and drained, or ``Failure(ChannelTimeoutError)``
    if a timeout is specified and expires. This makes "the channel is closed"
    a type-safe outcome rather than a second return value. Iterating over a
    channel yields its values until it is closed.

    Examples:
        >>> ch = Channel[int](capacity=1)
        >>> ch.send(42)
        >>> ch.recv()
        Success(42)
        >>> ch.close()
        >>> ch.recv()
        Failure(ChannelClosedError('recv on closed channel'))
    """

    def __init__(
        self,
        capacity: int = 0,
        *,
        backend: BaseThreadingBackend | None = None,
    ) -> None:
        """Initialize a channel.

        Args:
            capacity: Buffer size. ``0`` (the default) makes the channel
                unbuffered, so each send blocks for a matching receive.
                A positive value buffers that many pending values.
            backend: The threading backend whose condition variable
                coordinates senders and receivers. Defaults to the shared
                :func:`~katharos.concurrency.threading_backend.default_backend`.

        Raises:
            ValueError: If ``capacity`` is negative.
        """
        if capacity < 0:
            raise ValueError("capacity must be non-negative")

        self._backend = backend or default_backend()
        self._capacity = capacity
        self._buffer: deque[_Slot[A]] = deque()
        self._closed = False
        self._cond = self._backend.create_condition()

    @property
    def capacity(self) -> int:
        """The channel's buffer capacity (``0`` for an unbuffered channel)."""
        return self._capacity

    def send(self, value: A) -> None:
        """Send a value into the channel, blocking as needed.

        For a buffered channel this blocks while the buffer is full. For an
        unbuffered channel it blocks until another thread receives the value.

        Args:
            value: The value to send.

        Raises:
            ChannelClosedError: If the channel is (or becomes) closed before
                the value can be delivered.
        """
        with self._cond:
            if self._closed:
                raise ChannelClosedError("send on closed channel")

            if self._capacity > 0:
                while len(self._buffer) >= self._capacity and not self._closed:
                    self._cond.wait()
                if self._closed:
                    raise ChannelClosedError("send on closed channel")
                self._buffer.append(_Slot(value))
                self._cond.notify_all()
                return

            # Unbuffered: offer the value, then block until *this* slot is
            # taken by a receiver. Waiting on our own slot's identity (rather
            # than on the buffer being empty) keeps the hand-off correct when
            # multiple senders contend -- another sender refilling the buffer
            # can no longer be mistaken for our value being received.
            slot = _Slot(value)
            self._buffer.append(slot)
            self._cond.notify_all()

            while not slot.taken and not self._closed:
                self._cond.wait()
            if not slot.taken:
                # Closed before a receiver took the value; do not deliver it.
                try:
                    self._buffer.remove(slot)
                except ValueError:
                    pass
                raise ChannelClosedError("send on closed channel")

    def recv(
        self,
        timeout: float | None = None,
    ) -> Result[ChannelClosedError | ChannelTimeoutError, A]:
        """Receive a value, blocking until one is available or the channel closes.

        Args:
            timeout: Maximum seconds to wait for a value. ``None`` (default)
                blocks indefinitely. A positive float will return a
                ``ChannelTimeoutError`` failure if no value arrives in time.

        Returns:
            ``Success(value)`` when a value is received.
            ``Failure(ChannelClosedError)`` when the channel is closed and empty.
            ``Failure(ChannelTimeoutError)`` when the timeout expires.

        Examples:
            >>> ch = Channel[int](capacity=1)
            >>> ch.send(42)
            >>> ch.recv()
            Success(42)

            >>> ch = Channel[int]()
            >>> ch.close()
            >>> ch.recv()
            Failure(ChannelClosedError('recv on closed channel'))

            Timeout on an empty channel:

            >>> ch = Channel[int]()
            >>> ch.recv(timeout=0.01)
            Failure(ChannelTimeoutError('recv timed out after 0.01 seconds'))
        """

        def not_closed_but_has_no_buffer() -> bool:
            return not self._closed and not self._buffer

        with self._cond:
            # Track an absolute deadline so a notify-driven wakeup that loses the
            # value to another receiver does not re-arm the full timeout.
            deadline = None if timeout is None else time.monotonic() + timeout
            while not_closed_but_has_no_buffer():
                remaining = None if deadline is None else deadline - time.monotonic()
                if remaining is not None and remaining <= 0:
                    return Result[ChannelTimeoutError, A].Failure(
                        ChannelTimeoutError(f"recv timed out after {timeout} seconds")
                    )
                self._cond.wait(remaining)

            if not self._buffer:
                return Result[ChannelClosedError, A].Failure(
                    ChannelClosedError("recv on closed channel")
                )

            slot = self._buffer.popleft()
            slot.taken = True
            self._cond.notify_all()
            return Result[ChannelClosedError | ChannelTimeoutError, A].Success(
                slot.value
            )

    def close(self) -> None:
        """Close the channel.

        After closing, :meth:`send` raises :class:`ChannelClosedError` and
        :meth:`recv` returns the remaining buffered values followed by a
        ``Failure(ChannelClosedError)``. Any blocked senders or receivers
        are woken.

        Raises:
            ChannelClosedError: If the channel is already closed.
        """
        with self._cond:
            if self._closed:
                raise ChannelClosedError("close of closed channel")
            self._closed = True
            self._cond.notify_all()

    def __iter__(self) -> Iterator[A]:
        """Iterate over received values until the channel is closed and drained.

        Yields:
            Each received value, in order.
        """
        while True:
            received = self.recv()
            if received.is_failure():
                return
            yield received.unwrap()

    def __repr__(self) -> str:
        """Return a string representation of the channel."""
        state = "closed" if self._closed else "open"
        return f"Channel(capacity={self._capacity}, {state})"
