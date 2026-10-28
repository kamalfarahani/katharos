import threading
import time

import pytest

from katharos.concurrency.csp import ChannelClosedError, ChannelTimeoutError, csp
from katharos.types import Result

# The default runtime's channel supplies the backend automatically.
Channel = csp.Channel


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
    def test_recv_returns_success_of_sent_value(self):
        ch = Channel[int](capacity=1)
        sent = ch.send(42)
        assert sent.is_success()
        assert sent.unwrap() is None

        result = ch.recv()
        assert result.is_success()
        assert result.unwrap() == 42

    def test_recv_returns_result(self):
        ch = Channel[int](capacity=1)
        ch.send(1)

        assert isinstance(ch.recv(), Result)

    def test_preserves_fifo_order(self):
        ch = Channel[int](capacity=3)
        ch.send(1)
        ch.send(2)
        ch.send(3)

        assert ch.recv().unwrap() == 1
        assert ch.recv().unwrap() == 2
        assert ch.recv().unwrap() == 3

    def test_send_does_not_block_until_buffer_full(self):
        ch = Channel[int](capacity=2)
        ch.send(1)
        ch.send(2)  # should return without a receiver

        assert ch.recv().unwrap() == 1

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
        assert ch.recv().unwrap() == 1  # free a slot
        assert unblocked.wait(timeout=1)  # now the send completes
        t.join()


class TestUnbufferedChannel:
    def test_send_blocks_until_received(self):
        ch = Channel[int]()
        unblocked = threading.Event()

        outcomes = []

        def sender():
            outcomes.append(ch.send(7))
            unblocked.set()

        t = threading.Thread(target=sender)
        t.start()

        assert not unblocked.wait(timeout=0.1)  # no receiver yet, so blocked
        assert ch.recv().unwrap() == 7
        assert unblocked.wait(timeout=1)  # rendezvous complete
        t.join(timeout=1)
        assert outcomes[0].is_success()
        assert outcomes[0].unwrap() is None

    def test_received_value_always_unblocks_its_sender(self):
        # Regression: with two contending senders, an unbuffered send must
        # return once *its* value is received -- it must not wait on the
        # buffer being empty, which another sender can refill. Looped because
        # the offending interleaving is schedule-dependent.
        for _ in range(50):
            ch = Channel[int]()
            completed: list[int] = []
            lock = threading.Lock()

            def sender(value: int, ch=ch, lock=lock, completed=completed) -> None:
                ch.send(value)
                with lock:
                    completed.append(value)

            threads = [
                threading.Thread(target=sender, args=(v,), daemon=True) for v in (0, 1)
            ]
            for t in threads:
                t.start()

            try:
                time.sleep(0.005)
                ch.recv().unwrap()  # receive exactly one value

                # The sender of the received value must finish promptly.
                deadline = time.monotonic() + 1.0
                while time.monotonic() < deadline:
                    with lock:
                        if completed:
                            break
                    time.sleep(0.001)

                with lock:
                    assert completed, "a value was received but no send() completed"
            finally:
                ch.close()
                deadline = time.monotonic() + 1
                for thread in threads:
                    thread.join(timeout=max(0, deadline - time.monotonic()))
                assert all(not thread.is_alive() for thread in threads)

    def test_recv_blocks_until_sent(self):
        ch = Channel[int]()
        received: list[Result] = []

        def receiver():
            received.append(ch.recv())

        t = threading.Thread(target=receiver)
        t.start()

        time.sleep(0.1)
        assert received == []  # no value yet
        ch.send(9)
        t.join(timeout=1)
        assert len(received) == 1
        assert received[0].is_success()
        assert received[0].unwrap() == 9


class TestChannelClose:
    def test_recv_drains_buffer_then_returns_failure(self):
        ch = Channel[int](capacity=2)
        ch.send(1)
        ch.send(2)
        ch.close()

        assert ch.recv().unwrap() == 1
        assert ch.recv().unwrap() == 2
        result = ch.recv()
        assert result.is_failure()
        assert isinstance(result.error, ChannelClosedError)

    def test_recv_on_closed_empty_returns_failure(self):
        ch = Channel[int]()
        ch.close()

        result = ch.recv()
        assert result.is_failure()
        assert isinstance(result.error, ChannelClosedError)

    @pytest.mark.parametrize("capacity", [0, 1])
    def test_send_on_closed_returns_failure(self, capacity):
        ch = Channel[int](capacity=capacity)
        ch.close()

        result = ch.send(1)

        assert result.is_failure()
        assert isinstance(result.error, ChannelClosedError)
        assert str(result.error) == "send on closed channel"
        assert ch.recv().is_failure()

    @pytest.mark.parametrize("capacity", [0, 1])
    def test_blocked_senders_return_failure_on_close(self, capacity, monkeypatch):
        ch = Channel[int](capacity=capacity)
        if capacity:
            assert ch.send(0).is_success()
        waiting = threading.Event()
        waiting_senders = set()
        original_wait = ch._cond.wait
        outcomes = []

        def wait(timeout=None):
            waiting_senders.add(threading.get_ident())
            if len(waiting_senders) == 3:
                waiting.set()
            return original_wait(timeout)

        monkeypatch.setattr(ch._cond, "wait", wait)
        threads = [
            threading.Thread(
                target=lambda value=value: outcomes.append(ch.send(value)),
                daemon=True,
            )
            for value in (1, 2, 3)
        ]
        for thread in threads:
            thread.start()
        try:
            assert waiting.wait(timeout=1)
        finally:
            ch.close()
            for thread in threads:
                thread.join(timeout=1)

        assert all(not thread.is_alive() for thread in threads)
        assert len(outcomes) == 3
        for result in outcomes:
            assert result.is_failure()
            assert isinstance(result.error, ChannelClosedError)
            assert str(result.error) == "send on closed channel"
        # Only values accepted before closure may remain buffered.
        assert list(ch) == ([0] if capacity else [])

    def test_completed_handoff_succeeds_when_closed_before_sender_resumes(
        self, monkeypatch
    ):
        ch = Channel[int]()
        waiting = threading.Event()
        original_wait = ch._cond.wait
        outcomes = []

        def wait(timeout=None):
            waiting.set()
            return original_wait(timeout)

        monkeypatch.setattr(ch._cond, "wait", wait)
        thread = threading.Thread(
            target=lambda: outcomes.append(ch.send(7)), daemon=True
        )
        thread.start()
        try:
            assert waiting.wait(timeout=1)
            # The standard backend's condition uses an RLock. Hold it across
            # recv and close so the sender cannot resume between the two.
            with ch._cond:
                assert ch.recv().unwrap() == 7
                ch.close()
        finally:
            if not ch._closed:
                ch.close()
            thread.join(timeout=1)

        assert not thread.is_alive()
        assert len(outcomes) == 1
        assert outcomes[0].is_success()
        assert outcomes[0].unwrap() is None
        assert ch.recv().is_failure()

    def test_double_close_raises(self):
        ch = Channel[int]()
        ch.close()

        with pytest.raises(ChannelClosedError):
            ch.close()

    def test_blocked_receiver_unblocks_on_close(self):
        ch = Channel[int]()
        result: list[Result] = []

        def receiver():
            result.append(ch.recv())

        t = threading.Thread(target=receiver)
        t.start()
        time.sleep(0.1)
        ch.close()
        t.join(timeout=1)

        assert len(result) == 1
        assert result[0].is_failure()
        assert isinstance(result[0].error, ChannelClosedError)


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


class TestRecvTimeout:
    def test_recv_times_out_on_empty_channel(self):
        ch = Channel[int]()

        result = ch.recv(timeout=0.01)

        assert result.is_failure()
        assert isinstance(result.error, ChannelTimeoutError)

    def test_recv_with_none_timeout_blocks_indefinitely(self):
        ch = Channel[int]()
        received: list[Result] = []

        def receiver():
            received.append(ch.recv(timeout=None))

        t = threading.Thread(target=receiver)
        t.start()

        time.sleep(0.1)
        assert received == []  # still blocking
        ch.send(42)
        t.join(timeout=1)

        assert len(received) == 1
        assert received[0].is_success()
        assert received[0].unwrap() == 42

    def test_recv_returns_value_before_timeout(self):
        ch = Channel[int]()
        received: list[Result] = []

        def receiver():
            received.append(ch.recv(timeout=1.0))

        t = threading.Thread(target=receiver)
        t.start()

        time.sleep(0.1)
        ch.send(99)
        t.join(timeout=1)

        assert len(received) == 1
        assert received[0].is_success()
        assert received[0].unwrap() == 99

    def test_recv_with_buffered_channel_returns_immediately(self):
        ch = Channel[int](capacity=2)
        ch.send(1)
        ch.send(2)

        # Buffer has values, should return immediately even with short timeout
        result = ch.recv(timeout=0.001)
        assert result.is_success()
        assert result.unwrap() == 1

        result = ch.recv(timeout=0.001)
        assert result.is_success()
        assert result.unwrap() == 2

    def test_recv_timeout_on_empty_buffered_channel(self):
        ch = Channel[int](capacity=2)

        result = ch.recv(timeout=0.01)

        assert result.is_failure()
        assert isinstance(result.error, ChannelTimeoutError)
