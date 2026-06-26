import threading
import time

import pytest

from katharos.concurrency.csp import (
    ChannelClosedError,
    SelectResult,
    csp,
    recv,
    select,
)

# The default runtime's channel supplies the backend automatically.
Channel = csp.Channel
go = csp.go


class TestSelectReady:
    def test_returns_index_and_value_of_ready_channel(self):
        a = Channel[int](capacity=1)
        b = Channel[int](capacity=1)
        b.send(99)

        choice = select(recv(a), recv(b))

        assert isinstance(choice, SelectResult)
        assert choice.index == 1
        assert choice.channel is b
        assert choice.value.unwrap() == 99
        assert not choice.is_default
        assert not choice.is_timeout

    def test_first_ready_in_argument_order_wins(self):
        a = Channel[int](capacity=1)
        b = Channel[int](capacity=1)
        a.send(1)
        b.send(2)

        choice = select(recv(a), recv(b))

        assert choice.index == 0
        assert choice.value.unwrap() == 1

    def test_closed_channel_is_selected_as_failure(self):
        a = Channel[int]()
        a.close()

        choice = select(recv(a))

        assert choice.index == 0
        assert choice.value.is_failure()
        assert isinstance(choice.value.error, ChannelClosedError)


class TestSelectBlocking:
    def test_blocks_until_a_value_arrives(self):
        a = Channel[int]()
        b = Channel[int]()

        go(lambda: (time.sleep(0.05), b.send(7)))

        # A generous timeout bounds the wait: a regression in the wakeup path
        # surfaces as a clean timeout failure rather than hanging the suite.
        choice = select(recv(a), recv(b), timeout=1.0)

        assert not choice.is_timeout
        assert choice.index == 1
        assert choice.value.unwrap() == 7

    def test_blocked_select_woken_by_close(self):
        a = Channel[int]()

        go(lambda: (time.sleep(0.05), a.close()))

        choice = select(recv(a), timeout=1.0)

        assert not choice.is_timeout
        assert choice.index == 0
        assert choice.value.is_failure()
        assert isinstance(choice.value.error, ChannelClosedError)

    def test_unbuffered_handoff_completes_the_sender(self):
        ch = Channel[int]()
        sent = threading.Event()

        def sender():
            ch.send(123)
            sent.set()

        handle = go(sender)

        choice = select(recv(ch), timeout=1.0)

        assert not choice.is_timeout
        assert choice.index == 0
        assert choice.value.unwrap() == 123
        # The sender's blocking send returns once its value was taken.
        assert sent.wait(timeout=1.0)
        handle.join()


class TestSelectDefault:
    def test_default_returns_immediately_when_nothing_ready(self):
        a = Channel[int]()
        b = Channel[int]()

        choice = select(recv(a), recv(b), default=True)

        assert choice.is_default
        assert choice.index is None
        assert choice.channel is None
        assert choice.value is None

    def test_default_not_taken_when_a_channel_is_ready(self):
        a = Channel[int](capacity=1)
        a.send(5)

        choice = select(recv(a), default=True)

        assert not choice.is_default
        assert choice.index == 0
        assert choice.value.unwrap() == 5


class TestSelectTimeout:
    def test_times_out_when_nothing_arrives(self):
        a = Channel[int]()

        start = time.monotonic()
        choice = select(recv(a), timeout=0.05)
        elapsed = time.monotonic() - start

        assert choice.is_timeout
        assert choice.index is None
        assert choice.value is None
        assert elapsed >= 0.05

    def test_returns_value_when_it_arrives_before_timeout(self):
        a = Channel[int]()

        go(lambda: (time.sleep(0.02), a.send(42)))

        choice = select(recv(a), timeout=1.0)

        assert not choice.is_timeout
        assert choice.index == 0
        assert choice.value.unwrap() == 42


class TestSelectObserverCleanup:
    """A blocking select must unregister its observer on every exit path."""

    def test_observers_unregistered_after_blocking_value(self):
        a = Channel[int]()

        go(lambda: (time.sleep(0.05), a.send(7)))

        select(recv(a), timeout=1.0)  # goes through the register/wait path

        assert a._observers == []

    def test_observers_unregistered_after_timeout(self):
        a = Channel[int]()

        choice = select(recv(a), timeout=0.05)

        assert choice.is_timeout
        assert a._observers == []


class TestSelectValidation:
    def test_no_cases_without_default_or_timeout_raises(self):
        with pytest.raises(ValueError, match="block forever"):
            select()

    def test_no_cases_with_default_returns_default(self):
        assert select(default=True).is_default

    def test_no_cases_with_timeout_times_out(self):
        assert select(timeout=0.01).is_timeout


class TestSelectRepr:
    def test_repr_variants(self):
        a = Channel[int](capacity=1)
        a.send(1)
        assert "index=0" in repr(select(recv(a)))
        assert repr(select(default=True)) == "SelectResult(default)"
        assert repr(select(timeout=0.01)) == "SelectResult(timeout)"
