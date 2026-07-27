from __future__ import annotations

import time
from collections import deque
from collections.abc import Callable, Iterator
from typing import cast

from katharos.concurrency.base_threading_backend import BaseThreadingBackend
from katharos.types.result import Result


class ChannelClosedError(Exception):
    """Raised when sending on, or closing, an already-closed channel."""


class ChannelTimeoutError(Exception):
    """Raised when a channel operation times out."""


class NoValueInBufferError(Exception):
    """Raised when trying to receive from an empty buffer."""


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

    Note:
        Every :meth:`send`, :meth:`recv`, and :meth:`close` wakes *all*
        waiters (``notify_all``) to keep coordination correct under
        contention. This is O(number of waiters) per operation, so a single
        channel shared by a very large number of blocked senders/receivers
        trades throughput for simplicity.

    Examples:
        >>> from katharos.concurrency.threading_backend import ThreadingBackend
        >>> ch = Channel[int](capacity=1, backend=ThreadingBackend())
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
        backend: BaseThreadingBackend,
    ) -> None:
        """Initialize a channel.

        Args:
            capacity: Buffer size. ``0`` (the default) makes the channel
                unbuffered, so each send blocks for a matching receive.
                A positive value buffers that many pending values.
            backend: The threading backend whose condition variable
                coordinates senders and receivers.

        Raises:
            ValueError: If ``capacity`` is negative.
        """
        if capacity < 0:
            raise ValueError("capacity must be non-negative")

        self._backend = backend
        self._capacity = capacity
        self._buffer: deque[_Slot[A]] = deque()
        self._closed = False
        self._cond = self._backend.create_condition()
        self._observers: list[Callable[[], None]] = []

    @property
    def capacity(self) -> int:
        """The channel's buffer capacity (``0`` for an unbuffered channel)."""
        return self._capacity

    @property
    def backend(self) -> BaseThreadingBackend:
        """The threading backend coordinating this channel's senders and receivers."""
        return self._backend

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
                self._wake()
                return

            # Unbuffered: offer the value, then block until *this* slot is
            # taken by a receiver. Waiting on our own slot's identity (rather
            # than on the buffer being empty) keeps the hand-off correct when
            # multiple senders contend -- another sender refilling the buffer
            # can no longer be mistaken for our value being received.
            slot = _Slot(value)
            self._buffer.append(slot)
            self._wake()

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
            >>> from katharos.concurrency.threading_backend import ThreadingBackend
            >>> ch = Channel[int](capacity=1, backend=ThreadingBackend())
            >>> ch.send(42)
            >>> ch.recv()
            Success(42)

            >>> ch = Channel[int](backend=ThreadingBackend())
            >>> ch.close()
            >>> ch.recv()
            Failure(ChannelClosedError('recv on closed channel'))

            Timeout on an empty channel:

            >>> ch = Channel[int](backend=ThreadingBackend())
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

            # The loop only exits with a value buffered or the channel closed,
            # so _consume_locked never reports an empty buffer here.
            consumed = self._consume_locked()
            consumed = cast(Result[ChannelClosedError, A], consumed)
            return consumed

    def register_observer(self, callback: Callable[[], None]) -> None:
        """Register a callback notified when this channel changes state.

        Used by :func:`~katharos.concurrency.csp.select` to learn when a value
        becomes available (or the channel closes) without polling. The callback
        is invoked while this channel's internal lock is held, so it must do no
        more than set a flag and signal its own condition; it must never call
        back into this channel (doing so would deadlock the non-reentrant lock).

        Args:
            callback: A zero-argument callable invoked on each state change.
        """
        with self._cond:
            self._observers.append(callback)

    def unregister_observer(self, callback: Callable[[], None]) -> None:
        """Remove a callback previously registered with :meth:`register_observer`.

        Removing a callback that is not registered is a no-op.

        Args:
            callback: The callback to remove.
        """
        with self._cond:
            try:
                self._observers.remove(callback)
            except ValueError:
                pass

    def _wake(self) -> None:
        """Wake this channel's own waiters and any registered observers.

        Must be called while holding ``self._cond``; it does not re-acquire the
        lock. Observers are invoked in registration order (see
        :meth:`register_observer` for the callback contract).
        """
        self._cond.notify_all()
        for observer in self._observers:
            observer()

    def _consume_locked(
        self,
    ) -> Result[ChannelClosedError | NoValueInBufferError, A]:
        """Take the next ready outcome without blocking, assuming the lock is held.

        The buffer is checked before the closed flag so a closed-but-not-drained
        channel still yields its remaining values as ``Success`` before reporting
        closure.

        Returns:
            ``Success(value)`` if a value is buffered, ``Failure(ChannelClosedError)``
            if the channel is closed and drained, or ``Failure(NoValueInBufferError)``
            if the channel is open but empty (nothing ready).
        """
        if self._buffer:
            slot = self._buffer.popleft()
            slot.taken = True
            self._wake()
            return Result[ChannelClosedError | NoValueInBufferError, A].Success(
                slot.value
            )
        if self._closed:
            return Result[ChannelClosedError, A].Failure(
                ChannelClosedError("recv on closed channel")
            )

        return Result[NoValueInBufferError, A].Failure(
            NoValueInBufferError("recv on channel with no buffered values")
        )

    def _try_recv(
        self,
    ) -> Result[ChannelClosedError | NoValueInBufferError, A]:
        """Non-blocking :meth:`recv`: return the ready outcome without blocking.

        Acquires the channel lock briefly; unlike :meth:`recv` it never blocks.
        Used by :func:`~katharos.concurrency.csp.select` to poll readiness.

        Returns:
            ``Success(value)`` if a value is available, ``Failure(ChannelClosedError)``
            if closed and drained, or ``Failure(NoValueInBufferError)`` if the
            channel is open but empty.
        """
        with self._cond:
            return self._consume_locked()

    def close(self) -> None:
        """Close the channel.

        After closing, :meth:`send` raises :class:`ChannelClosedError` and
        :meth:`recv` returns the remaining buffered values followed by a
        ``Failure(ChannelClosedError)``. Any blocked senders or receivers
        are woken.

        Note:
            Closing an unbuffered channel while a sender is parked on an
            offered value races with any concurrent :meth:`recv`: that
            in-flight value is either handed to the receiver (the send then
            returns normally) or dropped (the send raises
            :class:`ChannelClosedError`), depending on which side next
            acquires the lock. As in Go, do not ``close`` a channel
            concurrently with a send you expect to complete.

        Raises:
            ChannelClosedError: If the channel is already closed.
        """
        with self._cond:
            if self._closed:
                raise ChannelClosedError("close of closed channel")
            self._closed = True
            self._wake()

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
