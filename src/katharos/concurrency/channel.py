from __future__ import annotations

import threading
from collections import deque
from collections.abc import Iterator

from katharos.types.maybe import Maybe


class ChannelClosedError(Exception):
    """Raised when sending on, or closing, an already-closed channel."""


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

    Unlike Go, :meth:`recv` returns a :class:`~katharos.types.Maybe`:
    ``Just(value)`` while values are available and ``Nothing`` once the
    channel is closed and drained. This makes "the channel is closed" a
    type-safe outcome rather than a second return value. Iterating over a
    channel yields its values until it is closed.

    Examples:
        >>> ch = Channel[int](capacity=1)
        >>> ch.send(42)
        >>> ch.recv()
        Just(42)
        >>> ch.close()
        >>> ch.recv()
        Nothing()
    """

    def __init__(self, capacity: int = 0) -> None:
        """Initialize a channel.

        Args:
            capacity: Buffer size. ``0`` (the default) makes the channel
                unbuffered, so each send blocks for a matching receive.
                A positive value buffers that many pending values.

        Raises:
            ValueError: If ``capacity`` is negative.
        """
        if capacity < 0:
            raise ValueError("capacity must be non-negative")

        self._capacity = capacity
        self._buffer: deque[A] = deque()
        self._closed = False
        self._cond = threading.Condition()

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
                self._buffer.append(value)
                self._cond.notify_all()
                return

            # Unbuffered: hand off one value at a time, then wait for receipt.
            while self._buffer and not self._closed:
                self._cond.wait()
            if self._closed:
                raise ChannelClosedError("send on closed channel")

            self._buffer.append(value)
            self._cond.notify_all()

            while self._buffer and not self._closed:
                self._cond.wait()
            if self._buffer:
                # Closed before the value was received; do not deliver it.
                self._buffer.clear()
                raise ChannelClosedError("send on closed channel")

    def recv(self) -> Maybe[A]:
        """Receive a value, blocking until one is available or the channel closes.

        Returns:
            ``Just(value)`` when a value is received, or ``Nothing`` once the
            channel is closed and no buffered values remain.
        """
        with self._cond:
            while not self._buffer and not self._closed:
                self._cond.wait()

            if not self._buffer:
                return Maybe.Nothing()

            value = self._buffer.popleft()
            self._cond.notify_all()
            return Maybe.Just(value)

    def close(self) -> None:
        """Close the channel.

        After closing, :meth:`send` raises :class:`ChannelClosedError` and
        :meth:`recv` returns the remaining buffered values followed by
        ``Nothing``. Any blocked senders or receivers are woken.

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
            if received.is_nothing():
                return
            yield received.unwrap()

    def __repr__(self) -> str:
        """Return a string representation of the channel."""
        state = "closed" if self._closed else "open"
        return f"Channel(capacity={self._capacity}, {state})"
