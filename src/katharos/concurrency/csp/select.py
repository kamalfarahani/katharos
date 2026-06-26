from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, cast

from katharos.concurrency.base_threading_backend import BaseThreadingBackend
from katharos.types.result import Result

from .channel import (
    Channel,
    ChannelClosedError,
    ChannelTimeoutError,
    NoValueInBufferError,
)


def _is_not_no_value_result(
    result: Result[
        ChannelClosedError | ChannelTimeoutError | NoValueInBufferError, Any
    ],
) -> bool:
    """
    Returns True if the result is not a NoValueInBufferError.

    Args:
        result: The result to check.

    Returns:
        True if the result is not a NoValueInBufferError, False otherwise.
    """
    if result.is_failure():
        return not isinstance(result.error, NoValueInBufferError)

    return True


class _RecvCase[A]:
    """A single ``select`` branch that receives from a channel.

    Constructed via :func:`recv`. Holds the channel and exposes a non-blocking
    poll used by :func:`select` to test readiness.
    """

    __slots__ = ("channel",)

    def __init__(self, channel: Channel[A]) -> None:
        self.channel = channel

    def poll(
        self,
    ) -> Result[ChannelClosedError | ChannelTimeoutError | NoValueInBufferError, A]:
        """Return the channel's outcome, or ``Failure(NoValueInBufferError)``.

        The ``NoValueInBufferError`` failure signals the case is not yet ready;
        :func:`select` treats any other outcome as ready.
        """
        return self.channel._try_recv()


def recv[A](channel: Channel[A]) -> _RecvCase[A]:
    """Build a receive case for :func:`select`.

    Args:
        channel: The channel to receive from when this case is chosen.

    Returns:
        A select case that, when ready, yields the result of receiving from
        ``channel``.

    Examples:
        >>> from katharos.concurrency.csp import csp, recv, select
        >>> ch = csp.Channel[int](capacity=1)
        >>> ch.send(7)
        >>> choice = select(recv(ch))
        >>> choice.index, choice.value.unwrap()
        (0, 7)
    """
    return _RecvCase(channel)


@dataclass(frozen=True)
class SelectResult[A]:
    """The outcome of a :func:`select` call.

    Exactly one of three things happened: a case became ready (``index``,
    ``channel`` and ``value`` are set), the ``default`` branch was taken
    (:attr:`is_default`), or the call timed out (:attr:`is_timeout`). In the
    latter two cases ``index``, ``channel`` and ``value`` are all ``None``.

    Attributes:
        index: Position (in argument order) of the chosen case, or ``None``.
        channel: The chosen case's channel, or ``None``.
        value: The chosen case's :class:`~katharos.types.Result`, or ``None``.
        is_default: Whether the ``default`` branch was taken.
        is_timeout: Whether the call timed out before any case was ready.
    """

    index: int | None = None
    channel: Channel[A] | None = None
    value: Result[ChannelClosedError | ChannelTimeoutError, A] | None = None
    is_default: bool = False
    is_timeout: bool = False

    def __repr__(self) -> str:
        """Return a string representation of the result."""
        if self.is_default:
            return "SelectResult(default)"
        if self.is_timeout:
            return "SelectResult(timeout)"
        return (
            f"SelectResult(index={self.index}, "
            f"channel={self.channel!r}, value={self.value!r})"
        )


class _Selector:
    """An auto-reset event shared by a single :func:`select` call.

    Registered as an observer on every channel in the call. Channels signal it
    (under their own lock) whenever they change state; :func:`select` blocks on
    it between polls. The retained ``_signaled`` flag closes the lost-wakeup
    window: a signal landing between a poll and a wait is seen, not missed.
    """

    __slots__ = ("_cond", "_signaled")

    def __init__(self, backend: BaseThreadingBackend) -> None:
        self._cond = backend.create_condition()
        self._signaled = False

    def signal(self) -> None:
        """Mark a state change and wake any waiter (the observer callback)."""
        with self._cond:
            self._signaled = True
            self._cond.notify_all()

    def wait_ready(self, timeout: float | None) -> bool:
        """Block until signaled or ``timeout`` elapses, consuming the signal.

        Args:
            timeout: Maximum seconds to wait, or ``None`` to wait indefinitely.

        Returns:
            ``True`` if a signal was pending or arrived, ``False`` on timeout.
        """
        with self._cond:
            if self._signaled:
                self._signaled = False
                return True
            return self._cond.wait(timeout)


def select[A](
    *cases: _RecvCase[A],
    default: bool = False,
    timeout: float | None = None,
) -> SelectResult[A]:
    """Wait for one of several channel operations to become ready.

    Mirrors Go's ``select``: given a number of cases (built with :func:`recv`),
    block until one is ready and return it. When several are ready at once, the
    first in argument order wins. A closed channel counts as ready (its case
    yields a ``Failure(ChannelClosedError)``).

    Args:
        *cases: The receive cases to wait on, in priority order.
        default: If ``True``, return immediately with a default result when no
            case is ready, instead of blocking. Mutually useful with, and takes
            precedence over, ``timeout``.
        timeout: Maximum seconds to block waiting for a case. ``None`` (the
            default) blocks indefinitely.

    Returns:
        A :class:`SelectResult`: the chosen case, the default branch, or a
        timeout.

    Raises:
        ValueError: If called with no cases and neither ``default`` nor
            ``timeout``, which would block forever.

    Examples:
        >>> from katharos.concurrency.csp import csp, recv, select
        >>> a = csp.Channel[int](capacity=1)
        >>> b = csp.Channel[int](capacity=1)
        >>> b.send(99)
        >>> choice = select(recv(a), recv(b))
        >>> choice.index, choice.value.unwrap()
        (1, 99)

        With ``default``, an empty channel does not block:

        >>> select(recv(a), default=True)
        SelectResult(default)
    """
    if not cases:
        if default:
            return SelectResult(is_default=True)
        if timeout is not None:
            # No channels means no backend to wait on and nothing can ever
            # become ready, so just honour the timeout directly.
            time.sleep(timeout)
            return SelectResult(is_timeout=True)

        raise ValueError("select with no cases would block forever")

    # Fast path: take a ready case (or the default) before registering observers.
    for index, case in enumerate(cases):
        ready = case.poll()
        if _is_not_no_value_result(ready):
            ready = cast(
                Result[ChannelClosedError | ChannelTimeoutError, A],
                ready,
            )
            return SelectResult(
                index=index,
                channel=case.channel,
                value=ready,
            )
    if default:
        return SelectResult(is_default=True)

    selector = _Selector(cases[0].channel._backend)
    for case in cases:
        case.channel.register_observer(selector.signal)
    try:
        deadline = None if timeout is None else time.monotonic() + timeout
        while True:
            # The poll is authoritative: a value that lands as wait_ready times
            # out is still caught here on the next iteration.
            for index, case in enumerate(cases):
                ready = case.poll()
                if _is_not_no_value_result(ready):
                    ready = cast(
                        Result[ChannelClosedError | ChannelTimeoutError, A],
                        ready,
                    )
                    return SelectResult(
                        index=index,
                        channel=case.channel,
                        value=ready,
                    )
            if deadline is None:
                remaining = None
            else:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return SelectResult(is_timeout=True)

            selector.wait_ready(remaining)
    finally:
        for case in cases:
            case.channel.unregister_observer(selector.signal)
