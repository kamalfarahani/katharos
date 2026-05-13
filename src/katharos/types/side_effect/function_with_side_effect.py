from dataclasses import dataclass
from typing import Callable


@dataclass
class FunctionWithSideEffect:
    f: Callable[[], None]
    description: str = ""

    @staticmethod
    def no_op() -> "FunctionWithSideEffect":
        """
        Return a no-op FunctionWithSideEffect instance.

        The returned instance wraps a function that ignores all arguments and
        performs no operation when called.
        """
        return FunctionWithSideEffect(
            f=lambda *args, **kwargs: None,
            description="No operation",
        )

    def __call__(self):
        self.f()

    def __rshift__(
        self,
        other: "FunctionWithSideEffect",
    ) -> "FunctionWithSideEffect":
        """
        Returns a new FunctionWithSideEffect that sequentially executes the function wrapped in `self`
        and then the function wrapped in `other`.

        Args:
            other: The FunctionWithSideEffect to execute sequentially.

        Returns:
            A new FunctionWithSideEffect that sequentially executes `self` and `other`.
        """

        def seq() -> None:
            self.f()
            other.f()

        return FunctionWithSideEffect(
            f=seq,
            description=f"{self.description};\n{other.description}",
        )
