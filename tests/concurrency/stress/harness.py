"""Thread supervision, bounded tracing, and test-only threading backends."""

from __future__ import annotations

import json
import random
import sys
import threading
import time
import traceback
from collections import deque
from dataclasses import asdict, dataclass
from pathlib import Path

from katharos.concurrency import ThreadingBackend
from katharos.concurrency.csp import Channel, ChannelClosedError


@dataclass(frozen=True)
class Case:
    scenario: str
    seed: int
    capacity: int
    backend: str
    producers: int = 2
    consumers: int = 2
    messages: int = 24
    fault: str | None = None


class PerturbedCondition(threading.Condition):
    """Valid condition with occasional spurious returns and scheduling yields."""

    def __init__(self, lock, seed):
        super().__init__(lock)
        self.rng = random.Random(seed)

    def __enter__(self):
        time.sleep(0)
        return super().__enter__()

    def wait(self, timeout=None):
        if self.rng.randrange(4) == 0:
            # A spurious return leaves the lock held, just like a real wake-up.
            return True
        return super().wait(timeout)


class TestBackend(ThreadingBackend):
    __test__ = False

    def __init__(self, mode, seed):
        self.mode = mode
        self.seed = seed
        self.created = 0

    def create_condition(self):
        self.created += 1
        if self.mode == "standard":
            return super().create_condition()
        lock = threading.Lock()
        if self.mode == "perturbed":
            return PerturbedCondition(lock, self.seed + self.created)
        return threading.Condition(lock)


class Context:
    def __init__(self, case: Case, trace_path: Path):
        self.case = case
        self.trace_path = trace_path
        self.backend = TestBackend(case.backend, case.seed)
        self.events = deque(maxlen=4096)
        self.lock = threading.Lock()
        self.flush_lock = threading.Lock()
        self.serial = 0
        self.report_fields = {}
        self.errors = []
        self.threads = []
        self.channels = []
        self.baseline_threads = set(threading.enumerate())
        self.last_progress = "created"
        self.checkpoint("created")

    def record(self, event, **fields):
        with self.lock:
            self.serial += 1
            serial = self.serial
            self.events.append(
                {
                    "id": serial,
                    "time_ns": time.monotonic_ns(),
                    "thread": threading.current_thread().name,
                    "event": event,
                    **fields,
                }
            )
        if serial % 256 == 0:
            self.flush()
        return serial

    def flush(self, **extra):
        with self.flush_lock:
            with self.lock:
                self.report_fields.update(extra)
                report = {
                    "case": asdict(self.case),
                    "python": sys.version,
                    "last_progress": self.last_progress,
                    "event_count": self.serial,
                    "events": list(self.events),
                    "worker_errors": list(self.errors),
                    **self.report_fields,
                }
            temporary = self.trace_path.with_suffix(".tmp")
            temporary.write_text(json.dumps(report, indent=2))
            temporary.replace(self.trace_path)

    def checkpoint(self, label):
        with self.lock:
            self.last_progress = label
        self.record("checkpoint", label=label)
        self.flush()

    def op(self, name, fn, *args, **kwargs):
        owner = getattr(fn, "__self__", None)
        operation = self.record(
            "invoke",
            operation=name,
            args=repr(args)[:160],
            channel=id(owner) if isinstance(owner, Channel) else None,
            cases=[id(arg.channel) for arg in args if hasattr(arg, "channel")],
        )
        try:
            result = fn(*args, **kwargs)
        except BaseException as exc:
            self.record("raise", operation_id=operation, outcome=repr(exc))
            raise
        self.record("complete", operation_id=operation, outcome=repr(result)[:160])
        return result

    def channel(self, capacity=None):
        channel = Channel(
            capacity=self.case.capacity if capacity is None else capacity,
            backend=self.backend,
        )
        self.channels.append(channel)
        return channel

    def spawn(self, name, fn):
        def work():
            try:
                fn()
            except BaseException:  # noqa: BLE001 - propagate every worker failure to parent
                error = traceback.format_exc()
                with self.lock:
                    self.errors.append(error)
                self.record("worker_error", error=error)

        thread = threading.Thread(target=work, name=name, daemon=True)
        self.threads.append(thread)
        thread.start()
        return thread

    def join(self, threads=None, timeout=5):
        deadline = time.monotonic() + timeout
        targets = self.threads if threads is None else threads
        for thread in targets:
            thread.join(max(0, deadline - time.monotonic()))
        alive = [thread.name for thread in targets if thread.is_alive()]
        assert not alive, f"workers did not finish: {alive}"
        assert not self.errors, "\n".join(self.errors)

    def finish(self):
        # Teardown itself is protected by the subprocess watchdog if a lock is stuck.
        for channel in self.channels:
            try:
                channel.close()
            except ChannelClosedError:
                pass
        self.join()
        assert not (set(threading.enumerate()) - self.baseline_threads), "thread leak"
        for channel in self.channels:
            with channel._cond:
                assert not channel._observers, "observer leak"
        self.checkpoint("finished")


def pause(rng, slow=False):
    if slow or rng.randrange(4) == 0:
        time.sleep(rng.random() * (0.0005 if slow else 0.00005))


def closed(result):
    assert result.is_failure()
    assert isinstance(result.error, ChannelClosedError)
