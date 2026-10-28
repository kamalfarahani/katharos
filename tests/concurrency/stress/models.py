"""Independent buffered-channel models, including bounded concurrent histories."""

from __future__ import annotations

import random
import threading
import time
from collections import deque
from functools import cache

from hypothesis import given, seed, settings
from hypothesis import strategies as st

from katharos.concurrency.csp import ChannelClosedError, ChannelTimeoutError


def linearizable(history, capacity, remaining=None):
    """Check every real-time-compatible ordering, pruning repeated states."""
    predecessors = [
        sum(
            1 << j
            for j, other in enumerate(history)
            if other["end"] < operation["start"]
        )
        for operation in history
    ]
    complete = (1 << len(history)) - 1

    @cache
    def visit(mask, queue, is_closed):
        if mask == complete:
            return remaining is None or queue == tuple(remaining)
        for index, operation in enumerate(history):
            bit = 1 << index
            if mask & bit or predecessors[index] & ~mask:
                continue
            kind, value, outcome = (
                operation["kind"],
                operation["value"],
                operation["outcome"],
            )
            updated, closed_next = queue, is_closed
            if kind == "send":
                if is_closed:
                    expected = ("closed", None)
                elif len(queue) < capacity:
                    expected = ("ok", None)
                    updated = (*queue, value)
                else:
                    continue
            elif kind == "recv":
                if queue:
                    expected = ("ok", queue[0])
                    updated = queue[1:]
                else:
                    expected = ("closed" if is_closed else "timeout", None)
            else:
                expected = ("closed" if is_closed else "ok", None)
                closed_next = True
            if outcome == expected and visit(mask | bit, updated, closed_next):
                return True
        return False

    return visit(0, (), False)


def sequential(ctx):
    """Generate nonblocking sequential operations against an independent deque."""

    @seed(ctx.case.seed)
    @settings(max_examples=25, deadline=None, database=None)
    @given(
        st.lists(
            st.tuples(
                st.sampled_from(("send", "recv", "close")),
                st.one_of(st.none(), st.integers(-4, 4)),
            ),
            min_size=1,
            max_size=60,
        )
    )
    def check(operations):
        capacity = max(1, ctx.case.capacity)
        channel = ctx.channel(capacity)
        queue = deque()
        is_closed = False
        for kind, value in operations:
            if kind == "send":
                if not is_closed and len(queue) == capacity:
                    # Blocking sends are covered by concurrent histories.
                    continue
                result = ctx.op("model-send", channel.send, value)
                if is_closed:
                    assert result.is_failure() and isinstance(
                        result.error, ChannelClosedError
                    )
                else:
                    assert result.is_success() and result.unwrap() is None
                    queue.append(value)
            elif kind == "recv":
                result = ctx.op("model-recv", channel.recv, timeout=0)
                if queue:
                    assert result.is_success() and result.unwrap() == queue.popleft()
                else:
                    error = ChannelClosedError if is_closed else ChannelTimeoutError
                    assert result.is_failure() and isinstance(result.error, error)
            else:
                try:
                    ctx.op("model-close", channel.close)
                except ChannelClosedError:
                    assert is_closed
                else:
                    assert not is_closed
                    is_closed = True
        if not is_closed:
            channel.close()
        assert list(channel) == list(queue)
        # Do not retain all generated channels until the end of the case.
        ctx.channels.remove(channel)

    check()


def histories(ctx):
    rng = random.Random(ctx.case.seed)
    for iteration in range(16):
        ctx.checkpoint(f"history {iteration}")
        capacity = rng.choice((1, 2, 3))
        channel = ctx.channel(capacity)
        history = []
        record_lock = threading.Lock()
        barrier = threading.Barrier(3)

        def worker(
            index,
            iteration=iteration,
            barrier=barrier,
            channel=channel,
            record_lock=record_lock,
            history=history,
        ):
            worker_rng = random.Random(ctx.case.seed + index + iteration * 7)
            barrier.wait(timeout=5)
            for step, kind in enumerate(("send", "recv", "send", "close")):
                value = index * 10 + step
                begin = time.monotonic_ns()
                if kind == "close":
                    try:
                        ctx.op("history-close", channel.close)
                        outcome = ("ok", None)
                    except ChannelClosedError:
                        outcome = ("closed", None)
                else:
                    result = (
                        ctx.op("history-send", channel.send, value)
                        if kind == "send"
                        else ctx.op("history-recv", channel.recv, timeout=0)
                    )
                    if result.is_success():
                        outcome = ("ok", result.unwrap())
                    else:
                        outcome = (
                            "closed"
                            if isinstance(result.error, ChannelClosedError)
                            else "timeout",
                            None,
                        )
                end = time.monotonic_ns()
                with record_lock:
                    history.append(
                        {
                            "kind": kind,
                            "value": value,
                            "outcome": outcome,
                            "start": begin,
                            "end": end,
                        }
                    )
                time.sleep(worker_rng.random() * 0.0001)

        workers = [
            ctx.spawn(f"history-{index}", lambda index=index: worker(index))
            for index in range(3)
        ]
        ctx.join(workers)
        ctx.record("history", capacity=capacity, operations=history)
        drained = list(channel)
        assert linearizable(history, capacity, remaining=drained), (
            f"non-linearizable history: {history}, remaining={drained}"
        )
