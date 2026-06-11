from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from types import TracebackType
from typing import Any

from katharos.types import ImmutableList, Promise


class BasePromiseScheduler(ABC):
    @abstractmethod
    def schedule(self, promises: Iterable[Promise[Any]]) -> None: ...

    @abstractmethod
    def start(self) -> None: ...

    @abstractmethod
    def wait(self) -> ImmutableList[Any]: ...

    @abstractmethod
    def cancel(self) -> None: ...

    @abstractmethod
    def __enter__(self) -> BasePromiseScheduler: ...

    @abstractmethod
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None: ...
