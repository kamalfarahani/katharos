import threading
import time

import pytest

from katharos.concurrency import Channel, ChannelClosedError
from katharos.types import Maybe


class TestChannelConstruction:
    def test_default_is_unbuffered(self):
        ch = Channel[int]()

        assert ch.capacity == 0

    def test_construction_with_capacity(self):
        ch = Channel[int](capacity=3)

        assert ch.capacity == 3

    def test_negative_capacity_raises(self):
        with pytest.raises(ValueError):
            Channel[int](capacity=-1)


class TestBufferedChannel:
    def test_recv_returns_just_of_sent_value(self):
        ch = Channel[int](capacity=1)
        ch.send(42)

        assert ch.recv() == Maybe.Just(42)

    def test_recv_returns_maybe(self):
        ch = Channel[int](capacity=1)
        ch.send(1)

        assert isinstance(ch.recv(), Maybe)

    def test_preserves_fifo_order(self):
        ch = Channel[int](capacity=3)
        ch.send(1)
        ch.send(2)
        ch.send(3)

        assert ch.recv() == Maybe.Just(1)
        assert ch.recv() == Maybe.Just(2)
        assert ch.recv() == Maybe.Just(3)

    def test_send_does_not_block_until_buffer_full(self):
        ch = Channel[int](capacity=2)
        ch.send(1)
        ch.send(2)  # should return without a receiver

        assert ch.recv() == Maybe.Just(1)

    def test_send_blocks_when_buffer_full(self):
        ch = Channel[int](capacity=1)
        ch.send(1)
        unblocked = threading.Event()

        def sender():
            ch.send(2)
            unblocked.set()

        t = threading.Thread(target=sender)
        t.start()

        assert not unblocked.wait(timeout=0.1)  # blocked, buffer is full
        assert ch.recv() == Maybe.Just(1)  # free a slot
        assert unblocked.wait(timeout=1)  # now the send completes
        t.join()


class TestUnbufferedChannel:
    def test_send_blocks_until_received(self):
        ch = Channel[int]()
        unblocked = threading.Event()

        def sender():
            ch.send(7)
            unblocked.set()

        t = threading.Thread(target=sender)
        t.start()

        assert not unblocked.wait(timeout=0.1)  # no receiver yet, so blocked
        assert ch.recv() == Maybe.Just(7)
        assert unblocked.wait(timeout=1)  # rendezvous complete
        t.join()

    def test_recv_blocks_until_sent(self):
        ch = Channel[int]()
        received: list[Maybe[int]] = []

        def receiver():
            received.append(ch.recv())

        t = threading.Thread(target=receiver)
        t.start()

        time.sleep(0.1)
        assert received == []  # no value yet
        ch.send(9)
        t.join(timeout=1)
        assert received == [Maybe.Just(9)]


class TestChannelClose:
    def test_recv_drains_buffer_then_returns_nothing(self):
        ch = Channel[int](capacity=2)
        ch.send(1)
        ch.send(2)
        ch.close()

        assert ch.recv() == Maybe.Just(1)
        assert ch.recv() == Maybe.Just(2)
        assert ch.recv() == Maybe.Nothing()

    def test_recv_on_closed_empty_returns_nothing(self):
        ch = Channel[int]()
        ch.close()

        assert ch.recv() == Maybe.Nothing()

    def test_send_on_closed_raises(self):
        ch = Channel[int](capacity=1)
        ch.close()

        with pytest.raises(ChannelClosedError):
            ch.send(1)

    def test_double_close_raises(self):
        ch = Channel[int]()
        ch.close()

        with pytest.raises(ChannelClosedError):
            ch.close()

    def test_blocked_receiver_unblocks_on_close(self):
        ch = Channel[int]()
        result: list[Maybe[int]] = []

        def receiver():
            result.append(ch.recv())

        t = threading.Thread(target=receiver)
        t.start()
        time.sleep(0.1)
        ch.close()
        t.join(timeout=1)

        assert result == [Maybe.Nothing()]


class TestChannelIteration:
    def test_iterates_values_until_closed(self):
        ch = Channel[int](capacity=3)
        ch.send(1)
        ch.send(2)
        ch.send(3)
        ch.close()

        assert list(ch) == [1, 2, 3]

    def test_iteration_consumes_concurrently_produced_values(self):
        ch = Channel[int]()

        def producer():
            for i in range(5):
                ch.send(i)
            ch.close()

        t = threading.Thread(target=producer)
        t.start()

        assert list(ch) == [0, 1, 2, 3, 4]
        t.join()
