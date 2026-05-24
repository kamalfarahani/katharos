from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar, cast  # noqa: F401

from katharos.algebra import Monad
from katharos.algebra.applicative.applicative import Applicative

from .function_with_side_effect import FunctionWithSideEffect

A = TypeVar("A", covariant=True)


class IO(Monad["IO[Any]", A]):
    """Lazy wrapper for a value with deferred side-effect execution.

    ``IO`` encapsulates a value together with an optional side-effect function.
    The side effect is not run until :meth:`execute` is called, preserving
    referential transparency for pure callers.

    Use :meth:`pure` or :meth:`ret` to create an ``IO`` with no side effect,
    :meth:`fmap` to transform the wrapped value, and ``|`` (or :meth:`bind`)
    to sequence computations. Call :meth:`execute` to run accumulated side
    effects.
    """

    io_func: FunctionWithSideEffect

    @classmethod
    def pure[T](cls, x: T) -> IO[T]:
        """Wrap a plain value in an IO action with no side effect.

        Args:
            x: The value to wrap.

        Returns:
            An IO action containing the given value.
        """
        return IO(x)

    @classmethod
    def ret[T](cls, x: T) -> IO[T]:
        """Wrap a plain value in an IO action with no side effect.

        Alias for :meth:`pure`, provided to satisfy the Monad interface.

        Args:
            x: The value to wrap.

        Returns:
            An IO action containing the given value.
        """
        return cls.pure(x)

    def __init__(
        self,
        value: A,
        io_func: FunctionWithSideEffect = FunctionWithSideEffect.no_op(),
    ):
        """Initialize an IO action.

        Args:
            value: The value to wrap.
            io_func: The side-effect function to defer. Defaults to a no-op.
        """
        self._value = value
        self.io_func = io_func

    @property
    def value(self) -> A:
        """The value inside this IO action.

        Returns:
            The wrapped value.
        """
        return self._value

    def execute(self) -> None:
        """Execute the accumulated side effects."""
        self.io_func.f()

    def fmap[B](self, f: Callable[[A], B]) -> IO[B]:
        """Map a function over the wrapped value.

        Args:
            f: Function to apply to the value.

        Returns:
            A new IO action containing the mapped value.
        """
        return self >> IO(f(self.value))

    def ap[B](
        self,
        wrapped_funcs: Applicative[IO, Callable[[A], B]],
    ) -> IO[B]:
        """Apply a function wrapped in IO to this IO action.

        Args:
            wrapped_funcs: An IO action containing a function to apply.

        Returns:
            A new IO action with the result of applying the function.
        """
        return self >> IO(wrapped_funcs.value(self.value))  # type: ignore

    def bind[B](
        self,
        f: Callable[[A], Monad[IO, B]],
    ) -> IO[B]:
        """Chain this IO action with a function that returns another IO action.

        Args:
            f: A function that takes the wrapped value and returns an IO action.

        Returns:
            A new IO action combining this action's side effects with those
            of the result of applying ``f``.
        """
        f = cast(Callable[[A], IO[B]], f)
        return self >> f(self.value)

    def then[B](self, other: Monad[IO, B]) -> IO[B]:
        """Sequence two IO actions, accumulating both side effects.

        Args:
            other: The IO action to sequence after this one.

        Returns:
            A new IO action that carries both side effects and holds
            the value of ``other``.
        """
        other = cast(IO[B], other)
        io = IO(
            value=other.value,
            io_func=self.io_func >> other.io_func,
        )

        return io

    def __pow__[B](
        self,
        wrapped_funcs: Applicative[IO, Callable[[A], B]],
    ) -> IO[B]:
        """Infix operator for applicative application (``**``).

        Args:
            wrapped_funcs: An IO action containing a function to apply.

        Returns:
            A new IO action with the result of applying the function.
        """
        return self.ap(wrapped_funcs)

    def __or__[B](self, f: Callable[[A], Monad[IO, B]]) -> IO[B]:
        """Infix operator for monadic bind (``|``).

        Args:
            f: A function that takes the wrapped value and returns an IO action.

        Returns:
            A new IO action with the result of applying ``f``.
        """
        return self.bind(f)

    def __rshift__[B](self, other: Monad[IO, B]) -> IO[B]:
        """Infix operator for sequencing IO actions (``>>``).

        Sequences this IO action with another, accumulating both side effects
        and discarding this action's value.

        Args:
            other: The IO action to sequence after this one.

        Returns:
            A new IO action carrying both side effects and holding
            ``other``'s value.
        """
        return self.then(other)
