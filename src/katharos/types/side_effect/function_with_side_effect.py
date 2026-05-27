from dataclasses import dataclass
from typing import Callable


@dataclass
class FunctionWithSideEffect:
    """A callable that wraps a side-effecting function with an optional description.

    Attributes:
        f: The zero-argument callable that performs the side effect.
        description: Human-readable label for the side effect.
    """

    f: Callable[[], None]
    description: str = ""

    @staticmethod
    def no_op() -> "FunctionWithSideEffect":
        """Return a no-op instance that performs no operation when called.

        Returns:
            A FunctionWithSideEffect wrapping a function that does nothing.
        """
        return FunctionWithSideEffect(
            f=lambda *args, **kwargs: None,
            description="No operation",
        )

    def __call__(self):
        """Invoke the wrapped side-effect function."""
        self.f()

    def __rshift__(
        self,
        other: "FunctionWithSideEffect",
    ) -> "FunctionWithSideEffect":
        """Return a new instance that runs this effect then ``other`` in sequence.

        Args:
            other: The effect to run after this one.

        Returns:
            A new FunctionWithSideEffect that executes both effects in order.
        """

        def seq() -> None:
            self.f()
            other.f()

        return FunctionWithSideEffect(
            f=seq,
            description=f"{self.description};\n{other.description}",
        )
