from dataclasses import dataclass
from typing import Callable


@dataclass
class FunctionWithSideEffect:
    func: Callable
    description: str = ""

    @staticmethod
    def no_op() -> "FunctionWithSideEffect":
        return FunctionWithSideEffect(
            func=lambda *args, **kwargs: None,
            description="No operation",
        )
