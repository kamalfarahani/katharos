from __future__ import annotations

from abc import ABC
from collections.abc import Callable
from typing import Any, Generic, TypeVar, cast

from katharos.algebra import Monad

A = TypeVar("A", covariant=True)
E = TypeVar("E", bound=Exception, covariant=True)


class Result(
    Generic[A, E],
    Monad["Result[Any, E]", A],
    ABC,
):
    """
    This class represents a computation that can either succeed with a value of type A
    or fail with an exception.

    It implements the Monad interface for error handling.
    """

    @classmethod
    def pure[T](cls: type[Result], x: T) -> Success[T, E]:
        """
        Wrap a value in a Success.

        Args:
            x: The value to wrap

        Returns:
            A Success containing the value
        """
        return Success(x)

    def fmap[B](self, f: Callable[[A], B]) -> Result[B, E]:
        """
        Map a function over the value.

        Args:
            f: Function to apply to the value

        Returns:
            Result[B]: Result containing the mapped value
        """
        raise NotImplementedError()

    def ap[B](  # type: ignore
        self,
        wrapped_funcs: Result[Callable[[A], B], E],
    ) -> Result[B, E]:
        """
        Apply a function wrapped in a Result to this Result.

        Args:
            wrapped_funcs: Result containing a function to apply

        Returns:
            Result[B]: Result of applying the function to this value
        """
        raise NotImplementedError()

    def bind[B](  # type: ignore
        self,
        f: Callable[[A], Result[B, E]],
    ) -> Result[B, E]:
        """
        Bind a function that returns a Result to this Result.

        Args:
            f: Function that takes a value of type A and returns a Result of type B

        Returns:
            Result[B]: Result of applying the function to this value
        """
        raise NotImplementedError()

    def __pow__[B](  # type: ignore
        self,
        wrapped_funcs: Result[Callable[[A], B], E],
    ) -> Result[B, E]:
        """
        Infix operator for applicative application.

        This enables the use of ** operator for applying functions in the context of Result.

        Args:
            wrapped_funcs: Result containing a function to apply

        Returns:
            Result[B]: Result of applying the function to this value
        """
        return self.ap(wrapped_funcs)

    def __or__[B](  # type: ignore
        self,
        f: Callable[[A], Result[B, E]],
    ) -> Result[B, E]:
        """
        Infix operator for bind.

        Args:
            f: A function that takes a value of type A and returns a Result of type B.

        Returns:
            Monad[B]: A Monad containing the result of applying the function to the value.
        """
        return self.bind(f)


class Failure(Result[A, E]):
    """
    This class represents a failed computation with an exception.
    """

    __match_args__ = ("error",)

    def __init__(self, error: E):
        """
        Initialize a Failure with an exception.

        Args:
            error: The exception that caused the failure
        """
        self._error = error

    def fmap[B](self, f: Callable[[A], B]) -> Result[B, E]:
        """
        Map a function over the error (no-op for Failure).

        Args:
            f: Function to apply (ignored for Failure)

        Returns:
            Self as Failure (no change)
        """
        return Failure[B, E](self._error)

    def ap[B](
        self,
        wrapped_funcs: Result[Callable[[A], B], E],
    ) -> Result[B, E]:
        """
        Apply a function wrapped in a Result to this Failure.

        Args:
            wrapped_funcs: Result containing a function to apply

        Returns:
            Self as Failure (no change)
        """
        return Failure[B, E](self._error)

    def bind[B](
        self,
        f: Callable[[A], Result[B, E]],
    ) -> Result[B, E]:
        """
        Bind a function that returns a Result to this Failure.

        Args:
            f: Function that takes a value and returns a Result

        Returns:
            Self as Failure (no change)
        """
        return Failure[B, E](self._error)

    @property
    def error(self) -> E:
        """
        Get the error contained in this Failure.

        Returns:
            The exception that caused the failure
        """
        return self._error

    def __repr__(self) -> str:
        """
        Return a string representation of this Failure.

        Returns:
            A string representation showing "Failure(exception)"
        """
        return f"Failure({self._error!r})"


class Success(Result[A, E]):
    """
    This class represents a successful computation with a value.
    """

    __match_args__ = ("value",)

    def __init__(self, value: A):
        """
        Initialize a Success with a value.

        Args:
            value: The successful result value
        """
        self._value = value

    def fmap[B](self, f: Callable[[A], B]) -> Success[B, E]:
        """
        Map a function over the value in this Success.

        Args:
            f: Function to apply to the value

        Returns:
            A new Success containing the result of applying f to the value
        """
        return Success(f(self._value))

    def ap[B](
        self,
        wrapped_funcs: Result[Callable[[A], B], E],
    ) -> Result[B, E]:
        """
        Apply a function wrapped in a Result to this Success.

        Args:
            wrapped_funcs: Result containing a function to apply

        Returns:
            A new Success with the result of applying the function
        """
        match wrapped_funcs:
            case Success(value=func):
                return Success(func(self._value))
            case Failure(error=e):
                return Failure[B, E](e)
            case _:
                raise TypeError("Unexpected pattern in ap")

    def bind[B](
        self,
        f: Callable[[A], Result[B, E]],
    ) -> Result[B, E]:
        """
        Bind a function that returns a Result to this Success.

        Args:
            f: Function that takes the value and returns a Result

        Returns:
            The result of applying f to the value
        """
        return f(self._value)

    @property
    def value(self) -> A:
        """
        Get the value contained in this Success.

        Returns:
            The successful result value
        """
        return self._value

    def __repr__(self) -> str:
        """
        Return a string representation of this Success.

        Returns:
            A string representation showing "Success(value)"
        """
        return f"Success({self._value!r})"
