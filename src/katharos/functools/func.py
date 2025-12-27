from __future__ import annotations

from typing import Callable


class Func[A, B]:
    """
    A thin, composable wrapper around a unary function `A -> B`.

    Provides helpers for applying the function, composing with other
    `Func` instances, and an identity function.
    """

    def __init__(self, f: Callable[[A], B]):
        """
        Initialize the function wrapper.

        Args:
            f: A callable that takes an `A` and returns a `B`.
        """
        self._func = f

    @property
    def func(self) -> Callable[[A], B]:
        """
        Return the underlying callable.

        Returns:
            The callable function.
        """
        return self._func

    def apply(self, x: A) -> B:
        """
        Apply the wrapped function to a single argument.

        Args:
            x: Argument of type `A`.

        Returns:
            The result of type `B`.
        """
        return self.func(x)

    def apply_args(self, *args):
        """
        Apply this object repeatedly to a sequence of arguments.

        Each step calls `result(arg)` where `result` starts as `self`.
        This assumes each intermediate result is itself callable.

        Args:
            *args: Positional arguments to apply in order.

        Returns:
            The final result after all applications.
        """
        result = self
        for arg in args:
            result = result(arg)

        return result

    def compose[C](self, other: Func[B, C]) -> Func[A, C]:
        """
        Compose this function with another `Func`.

        Args:
            other: A `Func` from `B` to `C`.

        Returns:
            A new `Func` from `A` to `C`.
        """

        def inner(x: A) -> C:
            return other.apply(self.apply(x))

        return Func(inner)

    def __call__(self, x: A) -> B:
        """
        Call the function with a single argument.

        Args:
            x: Argument of type `A`.

        Returns:
            The result of type `B`.
        """
        return self.apply(x)

    def __matmul__[C](self, other: Func[B, C]) -> Func[A, C]:
        """
        Compose this function with another `Func` using the `@` operator.

        Args:
            other: A `Func` from `B` to `C`.

        Returns:
            A new `Func` from `A` to `C`.
        """
        return self.compose(other)

    @staticmethod
    def id[A]() -> Func[A, A]:
        """
        Return the identity function on `A` wrapped in `Func`.
        """
        return Func(lambda x: x)
