from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from .function_with_side_effect import FunctionWithSideEffect
from .side_effect import SideEffect

A = TypeVar("A", covariant=True)


class IO(SideEffect[A]):
    """
    This class represents an I/O action that can be executed later.
    It encapsulates a value along with input and output side-effect functions.
    """

    io_func: FunctionWithSideEffect

    def __init__(
        self,
        value: A,
        io_func: FunctionWithSideEffect = FunctionWithSideEffect.no_op(),
    ):
        """
        Initialize an IO action.

        Args:
            func: Function to perform side effects (defaults to no operation)
        """
        super().__init__(value)
        self.io_func = io_func

    def execute(self) -> None:
        """
        Execute the IO action by running input and output functions.
        """
        self.io_func.f()

    def fmap[B](self, f: Callable[[A], B]) -> IO[B]:
        """
        Map a function over the value in this IO action.

        Args:
            f: Function to apply to the value

        Returns:
            A new IO action containing the result of applying f to the value
        """
        return super().fmap(f)

    def ap[B](self, wrapped_funcs: IO[Callable[[A], B]]) -> IO[B]:
        """
        Apply a function wrapped in IO to this IO action.
        Applies the function contained in wrapped_funcs to the value in this IO action.

        Args:
            wrapped_funcs: IO action containing a function to apply

        Returns:
            A new IO action with the result of applying the function
        """
        return IO(wrapped_funcs.value(self.value))

    def bind[B](self, f: Callable[[A], IO[B]]) -> IO[B]:
        """
        Bind a function that returns an IO action to this IO action.
        Applies the function f to the value in this IO action.

        Args:
            f: Function that takes the value and returns an IO action

        Returns:
            A new IO action with the result of applying f to the value
        """
        return super().bind(f)

    def sequence[B](self, other: IO[B]) -> IO[B]:
        """
        Sequence two monadic actions, discarding the result of the first.

        Args:
            other: The IO to sequence after this one.

        Returns:
            IO[B]: The result of the second IO.
        """
        io = IO(
            value=other.value,
            io_func=self.io_func >> other.io_func,
        )

        return io

    def __pow__[B](self, wrapped_funcs: IO[Callable[[A], B]]) -> IO[B]:
        """
        Infix operator for IO applicative functor.
        Applies a function wrapped in IO to this IO action.

        Args:
            wrapped_funcs: IO action containing a function to apply

        Returns:
            A new IO action with the result of applying the function
        """
        return self.ap(wrapped_funcs)

    def __or__[B](self, f: Callable[[A], IO[B]]) -> IO[B]:
        """
        Infix bind operator for IO actions.
        Applies the function f to the value inside this IO action.

        Args:
            f: Function that takes the value and returns an IO action

        Returns:
            A new IO action with the result of applying f to the value
        """
        return self.bind(f)

    def __rshift__[B](self, other: IO[B]) -> IO[B]:
        """
        Infix operator for sequencing IO actions.

        Sequences the first IO action with the second IO action, discarding
        the value of the first IO action.

        Args:
            other: The second IO action to sequence.

        Returns:
            A new IO action that contains the value of the second IO action.
        """
        return self.sequence(other)

    @classmethod
    def pure[T](cls, x: T) -> IO[T]:
        """
        Create an IO action that contains the given value.

        Args:
            x: The value to wrap in an IO action.

        Returns:
            IO[T]: An IO action containing the given value.
        """
        return IO(x)
