"""Channel accounting, race, selector, timeout, and resource scenarios."""

from __future__ import annotations

import gc
import importlib
import random
import threading
import time
import weakref
from collections import Counter
from dataclasses import replace
from types import SimpleNamespace

from katharos.concurrency.csp import (
    ChannelClosedError,
    ChannelTimeoutError,
    recv,
    select,
)
from katharos.types import Result

from .harness import Context, closed, pause


def delivery(ctx: Context, *, closing=False, mixed=False):
    case = ctx.case
    channels = [ctx.channel() for _ in range(3 if mixed else 1)]
    sent = [[] for _ in range(case.producers)]
    failed = [[] for _ in range(case.producers)]
    received = [[] for _ in range(case.consumers)]
    start = threading.Barrier(case.producers + case.consumers + 1)
    payloads = (None, 0, 0, object())
    if case.fault in ("drop", "duplicate"):
        channel = channels[0]
        original = channel.send

        def faulty_send(value):
            if case.fault == "drop":
                return Result.Success(None)
            original(value)
            return original(value)

        channel.send = faulty_send

    def produce(index):
        rng = random.Random(case.seed * 101 + index)
        start.wait(timeout=5)
        for sequence in range(case.messages):
            channel = channels[sequence % len(channels)]
            token = (index, sequence, payloads[sequence % len(payloads)])
            result = ctx.op("send", channel.send, token)
            if result.is_success():
                assert result.unwrap() is None
                sent[index].append(token[:2])
            else:
                closed(result)
                failed[index].append(token[:2])
            with channel._cond:
                if channel.capacity:
                    assert len(channel._buffer) <= channel.capacity, "capacity exceeded"
            pause(rng, slow=case.seed % 3 == 0)

    def consume(index):
        rng = random.Random(case.seed * 211 + index)
        start.wait(timeout=5)
        if mixed and index % 3 == 0:
            for token in channels[index % len(channels)]:
                ctx.record("iteration_value", token=repr(token)[:100])
                received[index].append(token[:2])
            return
        active = (
            list(channels)
            if mixed and index % 3 == 1
            else [channels[index % len(channels)]]
        )
        while active:
            if mixed and index % 3 == 1:
                # Include a duplicate case and reverse priority on alternating workers.
                cases = active if index % 2 else list(reversed(active))
                cases = cases + cases[:1]
                choice = ctx.op(
                    "select", select, *(recv(c) for c in cases), timeout=0.02
                )
                if choice.is_timeout:
                    continue
                assert choice.channel is cases[choice.index]
                result = choice.value
                channel = choice.channel
            else:
                channel = active[0]
                result = ctx.op("recv", channel.recv, timeout=0.02)
                if result.is_failure() and isinstance(
                    result.error, ChannelTimeoutError
                ):
                    continue
            if result.is_failure():
                closed(result)
                active.remove(channel)
            else:
                token = result.unwrap()
                assert token[2] is payloads[token[1] % len(payloads)], (
                    "payload identity"
                )
                received[index].append(token[:2])
            pause(rng, slow=case.seed % 3 == 1)

    consumers = [
        ctx.spawn(f"receiver-{i}", lambda i=i: consume(i))
        for i in range(case.consumers)
    ]
    producers = [
        ctx.spawn(f"sender-{i}", lambda i=i: produce(i)) for i in range(case.producers)
    ]
    start.wait(timeout=5)
    ctx.checkpoint("traffic started")
    if closing:
        time.sleep(random.Random(case.seed).random() * 0.005)
        closers_start = threading.Barrier(4)
        outcomes = []

        def close_all():
            closers_start.wait(timeout=5)
            for channel in channels:
                try:
                    ctx.op("close", channel.close)
                    outcomes.append((id(channel), True))
                except ChannelClosedError:
                    outcomes.append((id(channel), False))

        closers = [ctx.spawn(f"closer-{i}", close_all) for i in range(3)]
        closers_start.wait(timeout=5)
        ctx.join(closers)
        for channel in channels:
            assert sum(ok for identity, ok in outcomes if identity == id(channel)) == 1
    ctx.join(producers)
    if not closing:
        for channel in channels:
            ctx.op("close", channel.close)
    ctx.join(consumers)
    # Drain any channels not assigned a receiver in smaller topologies.
    for channel in channels:
        received.append([token[:2] for token in channel])
    accepted = Counter(token for batch in sent for token in batch)
    rejected = {token for batch in failed for token in batch}
    delivered = Counter(token for batch in received for token in batch)
    assert delivered == accepted, (
        f"delivery mismatch: sent={accepted}, received={delivered}"
    )
    assert not (rejected & delivered.keys()), "failed send was delivered"
    assert all(count == 1 for count in delivered.values()), "duplicate delivery"
    if case.consumers == 1 and not mixed:
        for producer in range(case.producers):
            sequences = [seq for pid, seq in received[0] if pid == producer]
            assert sequences == sorted(sequences), "per-producer FIFO violation"
    for channel in channels:
        closed(channel.send(None))
        closed(channel.recv(timeout=0))


def closure(ctx):
    # Park senders before closure when empty/partial/full capacity permits it.
    for fill in sorted({0, max(0, ctx.case.capacity - 1), ctx.case.capacity}):
        channel = ctx.channel()
        for value in range(fill):
            assert channel.send(("accepted", value)).is_success()
        waiting = threading.Event()
        original_wait = channel._cond.wait

        def wait(timeout=None, waiting=waiting, original_wait=original_wait):
            waiting.set()
            return original_wait(timeout)

        channel._cond.wait = wait
        outcomes = []
        count = max(2, ctx.case.producers)
        senders = [
            ctx.spawn(
                f"blocked-{i}",
                lambda i=i, outcomes=outcomes, channel=channel: outcomes.append(
                    (i, ctx.op("send", channel.send, ("inflight", i)))
                ),
            )
            for i in range(count)
        ]
        # An empty buffer may accept some senders. Ensure enough sends to fill it.
        if channel.capacity >= count + fill:
            ctx.join(senders)
        else:
            assert waiting.wait(timeout=5), "no sender parked"
        channel.close()
        ctx.join(senders)
        drained = list(channel)
        expected = [("accepted", value) for value in range(fill)]
        expected += [("inflight", i) for i, result in outcomes if result.is_success()]
        assert Counter(drained) == Counter(expected), "undelivered offer leaked"
        for _, result in outcomes:
            if result.is_failure():
                closed(result)
        closed(channel.recv(timeout=0))
    # Explicitly wake a population of receivers on an empty channel.
    channel = ctx.channel()
    outcomes = []
    waiting_receivers = set()
    all_waiting = threading.Event()
    receiver_wait = channel._cond.wait

    def wait_for_close(timeout=None):
        waiting_receivers.add(threading.get_ident())
        if len(waiting_receivers) == ctx.case.consumers:
            all_waiting.set()
        return receiver_wait(timeout)

    channel._cond.wait = wait_for_close
    receivers = [
        ctx.spawn(f"empty-{i}", lambda: outcomes.append(channel.recv()))
        for i in range(ctx.case.consumers)
    ]
    assert all_waiting.wait(timeout=5), "receivers did not park"
    channel.close()
    ctx.join(receivers)
    assert len(outcomes) == ctx.case.consumers
    for result in outcomes:
        closed(result)
    original_case = ctx.case
    # Keep soak traffic plus its three concurrent closers below 64 workers.
    ctx.case = replace(
        ctx.case,
        producers=min(30, ctx.case.producers),
        consumers=min(30, ctx.case.consumers),
    )
    try:
        delivery(ctx, closing=True)
    finally:
        ctx.case = original_case


def handoff(ctx):
    for deliver in (False, True):
        channel = ctx.channel(0)
        waiting = threading.Event()
        parked = threading.Event()
        resume = threading.Event()
        original_wait = channel._cond.wait

        def wait(
            timeout=None,
            waiting=waiting,
            original_wait=original_wait,
            deliver=deliver,
            channel=channel,
            parked=parked,
            resume=resume,
        ):
            waiting.set()
            result = original_wait(timeout)
            if deliver:
                # Pause after a wake without holding the lock: valid for Lock
                # and RLock backends, and independent of receiver scheduling.
                channel._cond.release()
                try:
                    parked.set()
                    assert resume.wait(timeout=5)
                finally:
                    channel._cond.acquire()
            return result

        channel._cond.wait = wait
        results = []
        sender = ctx.spawn(
            "handoff",
            lambda results=results, channel=channel: results.append(
                ctx.op("send", channel.send, None)
            ),
        )
        assert waiting.wait(timeout=5)
        assert not results, "unbuffered send completed without a receive"
        if deliver:
            assert channel.recv(timeout=1).unwrap() is None
            assert parked.wait(timeout=5)
        channel.close()
        resume.set()
        ctx.join([sender])
        assert len(results) == 1
        if deliver:
            assert results[0].is_success() and results[0].unwrap() is None
        else:
            closed(results[0])
        closed(channel.recv(timeout=0))


def timeouts(ctx):
    channel = ctx.channel(1)
    for timeout in (0, 0.001):
        result = channel.recv(timeout=timeout)
        assert result.is_failure() and isinstance(result.error, ChannelTimeoutError)
        assert select(recv(channel), timeout=timeout).is_timeout
        assert select(recv(channel), default=True, timeout=timeout).is_default
        assert channel.send(None).is_success()
        assert channel.recv(timeout=timeout).unwrap() is None
    channel.close()
    closed(channel.recv(timeout=0))
    closed(select(recv(channel), timeout=0).value)

    # Isolate clock substitution in this child and restore it before teardown.
    channel_module = importlib.import_module("katharos.concurrency.csp.channel")
    select_module = importlib.import_module("katharos.concurrency.csp.select")
    channel = ctx.channel(1)
    original_clock = channel_module.time
    now = [0.0]
    remaining = []
    original_wait = channel._cond.wait

    def wake(timeout=None):
        remaining.append(timeout)
        now[0] += 0.25
        # Model a contested wake: an offer appears and another receiver takes
        # it while the original waiter has temporarily released the lock.
        channel._cond.release()
        try:
            assert channel.send("stolen").is_success()
            assert channel.recv(timeout=0).unwrap() == "stolen"
        finally:
            channel._cond.acquire()
        return True

    channel._cond.wait = wake
    channel_module.time = SimpleNamespace(monotonic=lambda: now[0])
    try:
        result = channel.recv(timeout=1)
        assert isinstance(result.error, ChannelTimeoutError)
        assert remaining == [1, 0.75, 0.5, 0.25], f"deadline reset: {remaining}"
    finally:
        channel_module.time = original_clock
        channel._cond.wait = original_wait

    original_selector = select_module._Selector
    now[0] = 0
    remaining.clear()

    class FakeSelector(original_selector):
        def wait_ready(self, timeout):
            remaining.append(timeout)
            now[0] += 0.25
            if ctx.case.fault == "reset-timeout":
                now[0] = 0
                time.sleep(0.001)
            return True

    select_module._Selector = FakeSelector
    select_module.time = SimpleNamespace(monotonic=lambda: now[0])
    try:
        assert select(recv(channel), timeout=1).is_timeout
        assert remaining == [1, 0.75, 0.5, 0.25]
    finally:
        select_module._Selector = original_selector
        select_module.time = original_clock

    # Real delivery/closure/deadline races for both receive entry points.
    for index in range(8):
        for use_select in (False, True):
            channel = ctx.channel(1)

            def delayed(channel=channel, index=index):
                time.sleep((index % 3) * 0.001)
                if index % 4:
                    assert channel.send(index).is_success()
                channel.close()

            worker = ctx.spawn("deadline-delivery", delayed)
            if use_select:
                choice = ctx.op("deadline-select", select, recv(channel), timeout=0.001)
                result = None if choice.is_timeout else choice.value
                timed_out = choice.is_timeout
                if not timed_out:
                    assert choice.index == 0 and choice.channel is channel
            else:
                result = ctx.op("deadline-recv", channel.recv, timeout=0.001)
                timed_out = result.is_failure() and isinstance(
                    result.error, ChannelTimeoutError
                )
            ctx.join([worker])
            rest = list(channel)
            expected = [index] if index % 4 else []
            if timed_out:
                assert rest == expected, "timeout consumed a value"
            elif result.is_success():
                assert result.unwrap() == index and rest == [] and expected
            else:
                closed(result)
                assert expected == rest == []


def selectors(ctx):
    # Priority and duplicate cases when readiness is established before the call.
    a, b = ctx.channel(1), ctx.channel(1)
    a.send(1)
    b.send(2)
    choice = select(recv(b), recv(a), recv(b), default=True)
    assert choice.index == 0 and choice.channel is b and choice.value.unwrap() == 2
    assert a.recv(timeout=0).unwrap() == 1

    # Force state changes at registration, after the authoritative poll, and
    # immediately before waiting; no producer thread timing is needed.
    module = importlib.import_module("katharos.concurrency.csp.select")
    for phase in ("register", "poll", "wait"):
        channel = ctx.channel(1)
        register = channel.register_observer
        poll = channel._try_recv
        selector = module._Selector
        polls = [0]
        injected = [False]

        def offer(channel=channel, injected=injected):
            if not injected[0]:
                injected[0] = True
                assert channel.send(42).is_success()

        def register_and_offer(callback, register=register, phase=phase, offer=offer):
            if phase == "register":
                offer()  # No observer exists yet: the authoritative re-poll must see it.
            register(callback)

        def poll_and_offer(poll=poll, polls=polls, phase=phase, offer=offer):
            result = poll()
            polls[0] += 1
            if phase == "poll" and polls[0] == 2:
                offer()
            return result

        class GatedSelector(selector):
            def wait_ready(self, timeout, phase=phase, offer=offer):
                if phase == "wait":
                    offer()
                return super().wait_ready(timeout)

        channel.register_observer = register_and_offer
        channel._try_recv = poll_and_offer
        module._Selector = GatedSelector
        try:
            choice = select(recv(channel), recv(channel), timeout=0.2)
            assert not choice.is_timeout
            assert choice.index == 0 and choice.value.unwrap() == 42
            assert not channel._observers
        finally:
            module._Selector = selector

    # Registration can fail after an earlier channel already registered.
    a, b = ctx.channel(1), ctx.channel(1)

    original_register = b.register_observer

    def fail_registration(callback):
        original_register(callback)
        raise RuntimeError("injected registration failure")

    b.register_observer = fail_registration
    try:
        select(recv(a), recv(b), timeout=0.01)
    except RuntimeError as exc:
        assert str(exc) == "injected registration failure"
    else:
        raise AssertionError("registration failure swallowed")
    assert not a._observers and not b._observers

    # Keep at least one selector, iterator, and direct receiver on three channels.
    original_case = ctx.case
    ctx.case = replace(ctx.case, consumers=max(6, ctx.case.consumers))
    try:
        delivery(ctx, mixed=True)
        ctx.case = replace(
            ctx.case,
            producers=min(30, ctx.case.producers),
            consumers=min(30, ctx.case.consumers),
        )
        delivery(ctx, mixed=True, closing=True)
    finally:
        ctx.case = original_case


class Payload:
    pass


def lifecycle(ctx):
    try:
        import resource
    except ImportError:
        resource = None
    if resource is not None:
        ctx.record(
            "rss_before", maxrss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        )
    for _ in range(20):
        channel = ctx.channel(1)
        value = Payload()
        reference = weakref.ref(value)
        assert channel.send(value).is_success()
        del value
        assert channel.recv(timeout=0).is_success()
        gc.collect()
        assert reference() is None, "consumed payload retained"
        for _ in range(4):
            assert select(recv(channel), timeout=0.0001).is_timeout
            assert not channel._observers
        channel.close()
        rejected = Payload()
        reference = weakref.ref(rejected)
        closed(channel.send(rejected))
        del rejected
        gc.collect()
        assert reference() is None, "rejected payload retained"
        closed(select(recv(channel), timeout=0).value)
    # Offered unbuffered payloads must be released on failed sends too.
    channel = ctx.channel(0)
    value = Payload()
    reference = weakref.ref(value)
    entered = threading.Event()
    original_wait = channel._cond.wait

    def wait(timeout=None):
        entered.set()
        return original_wait(timeout)

    channel._cond.wait = wait
    results = []
    sender = ctx.spawn(
        "payload", lambda value=value: results.append(channel.send(value))
    )
    del value
    assert entered.wait(timeout=5)
    channel.close()
    ctx.join([sender])
    closed(results[0])
    gc.collect()
    assert reference() is None, "undelivered payload retained"
    if resource is not None:
        ctx.record(
            "rss_after", maxrss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        )


def missing_notification(ctx):
    channel = ctx.channel(0)
    ready = threading.Event()
    original_wait = channel._cond.wait

    def wait(timeout=None):
        ready.set()
        return original_wait(timeout)

    channel._cond.wait = wait
    sender = ctx.spawn("never-notified", lambda: channel.send(1))
    assert ready.wait(timeout=5)
    channel._wake = lambda: None
    assert channel.recv(timeout=0).unwrap() == 1
    ctx.join([sender], timeout=20)


def observer_fault(ctx):
    channel = ctx.channel(1)
    channel.unregister_observer = lambda callback: None
    assert select(recv(channel), timeout=0.001).is_timeout
    assert not channel._observers, "observer leak"


SCENARIOS = {
    "delivery": delivery,
    "closure": closure,
    "handoff": handoff,
    "timeouts": timeouts,
    "select": selectors,
    "lifecycle": lifecycle,
}
