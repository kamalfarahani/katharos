from __future__ import annotations

from collections.abc import Iterable
from concurrent.futures import Future, ThreadPoolExecutor
from types import TracebackType
from typing import Any

from katharos.types import ImmutableList, Promise

from .base_promise_scheduler import BasePromiseScheduler


class ThreadPoolPromiseScheduler(BasePromiseScheduler):
    def __init__(self, max_workers: int | None = None) -> None:
        self._max_workers = max_workers
        self._executor: ThreadPoolExecutor | None = None
        self._futures: ImmutableList[Future[Any]] = ImmutableList.identity()

    def schedule(self, promises: Iterable[Promise[Any]]) -> None:
        if self._executor is None:
            raise RuntimeError(
                "Scheduler not started. Use as a context manager or call start() first."
            )

        new_futures: ImmutableList[Future[Any]] = ImmutableList(
            [self._executor.submit(p.execute) for p in promises]
        )
        self._futures = self._futures + new_futures

    def start(self) -> None:
        self._executor = ThreadPoolExecutor(max_workers=self._max_workers)
        self._futures = ImmutableList.identity()

    def wait(self) -> ImmutableList[Any]:
        return ImmutableList([f.result() for f in self._futures])

    def cancel(self) -> None:
        for future in self._futures:
            future.cancel()
        self._futures = ImmutableList.identity()

    def __enter__(self) -> ThreadPoolPromiseScheduler:
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        if exc_type is None:
            self.wait()
        else:
            self.cancel()

        if self._executor is not None:
            self._executor.shutdown(wait=False)
            self._executor = None

        return None
