from __future__ import annotations

from collections.abc import Callable
from typing import Any, Generic, TypeVar, cast, final

from katharos.algebra import Monad
from katharos.algebra.applicative.applicative import Applicative

A = TypeVar("A", covariant=True)
E = TypeVar("E", bound=BaseException, covariant=True)


@final
class Result(
    Generic[A, E],
    Monad["Result[Any, E]", A],
):
    """
    A Result monad for error handling without exceptions.

    The Result type encapsulates a computation that can either succeed with a value
    of type A or fail with an exception of type E. It implements the Monad, Applicative,
    and Functor interfaces for composable error handling.

    A Result can be in one of two states:
    - Success: Contains a value of type A (non-exception)
    - Failure: Contains an exception of type E

    Type Parameters:
        A: The type of the success value
        E: The type of the exception (must be a subclass of BaseException)

    Examples:
        >>> success = Result.Success(42)
        >>> success.is_success()
        True
        >>> success
        Success(42)
        >>> success.value
        42

        >>> failure = Result.Failure(ValueError("error"))
        >>> failure.is_failure()
        True
        >>> failure
        Failure(ValueError('error'))
        >>> failure.error
        ValueError('error')

        >>> success.fmap(lambda x: x * 2)
        Success(84)

        >>> failure.fmap(lambda x: x * 2)
        Failure(ValueError('error'))

        >>> Result.Success(5) | (lambda x: Result.Success(x + 1))
        Success(6)

    Note:
        This class is marked as @final and cannot be subclassed. Use `is_success()`
        and `is_failure()` methods to check the state instead of type checking.
        Use `Result.Success()` to create success values and `Result.Failure()` to
        create failure values. Access success values with `.value` and failure
        errors with `.error`.
        The class supports the following operators:
        - `|` (pipe): Monadic bind operation
        - `**` (power): Applicative application
    """

    @classmethod
    def pure[T](cls: type[Result], x: T) -> Result[T, E]:
        """
        Wrap a value in a Success.

        Args:
            x: The value to wrap

        Returns:
            A Success containing the value

        Raises:
            TypeError: If the value is an exception
        """
        if isinstance(x, BaseException):
            raise TypeError("Cannot create a Result with an exception as the value")

        return Result(x)

    @staticmethod
    def Success(x: A) -> Result[A, E]:  # type: ignore
        """
        Create a Success result.

        Args:
            x: The value to wrap

        Returns:
            A Success result containing the value
        """
        return Result.pure(x)

    @staticmethod
    def Failure(e: E) -> Result[A, E]:  # type: ignore
        """
        Create a Failure result.

        Args:
            e: The exception to wrap

        Returns:
            A Failure result containing the exception
        """
        if not isinstance(e, BaseException):
            raise TypeError("Cannot create a Result with a non-exception as the value")

        return Result(e)

    def __init__(self, value: A | E) -> None:
        """
        Initialize the Result.

        Args:
            value: The value to wrap, either A or E
        """
        self._value = value

    @property
    def value(self) -> A:
        """
        Get the value of the Result.

        Returns:
            The value of the Result

        Raises:
            TypeError: If the Result is a Failure
        """
        if isinstance(self._value, BaseException):
            raise TypeError("Cannot get the value of a Failure")

        return self._value

    @property
    def error(self) -> E:
        """
        Get the error of the Result.

        Returns:
            The error of the Result

        Raises:
            TypeError: If the Result is a Success
        """
        if not isinstance(self._value, BaseException):
            raise TypeError("Cannot get the error of a Success")

        return cast(E, self._value)

    def fmap[B](self, f: Callable[[A], B]) -> Result[B, E]:
        """
        Map a function over the value.

        Args:
            f: Function to apply to the value

        Returns:
            Result[B]: Result containing the mapped value
        """
        if isinstance(self._value, BaseException):
            casted_self = cast(Result[B, E], self)
            return casted_self

        return Result(f(self._value))

    def ap[B](
        self,
        wrapped_funcs: Applicative[Result[Any, E], Callable[[A], B]],
    ) -> Result[B, E]:
        """
        Apply a function wrapped in a Result to this Result.

        Args:
            wrapped_funcs: Result containing a function to apply

        Returns:
            Result[B]: Result of applying the function to this value
        """
        wrapped_funcs = cast(Result[Callable[[A], B], E], wrapped_funcs)
        if isinstance(self._value, BaseException):
            result_err = cast(Result[B, E], self)
            return result_err

        if isinstance(wrapped_funcs._value, BaseException):
            result_err = cast(Result[B, E], wrapped_funcs)
            return result_err

        casted_self = cast(A, self._value)
        inner_func = cast(Callable[[A], B], wrapped_funcs._value)

        return Result(inner_func(casted_self))

    def bind[B](
        self,
        f: Callable[[A], Monad[Result[Any, E], B]],
    ) -> Result[B, E]:
        """
        Bind a function that returns a Result to this Result.

        Args:
            f: Function that takes a value of type A and returns a Result of type B

        Returns:
            Result[B]: Result of applying the function to this value
        """
        f = cast(Callable[[A], Result[B, E]], f)
        if isinstance(self._value, BaseException):
            return Result[B, E](self._value)  # type: ignore

        return f(self._value)

    def is_success(self) -> bool:
        """
        Check if this Result is a Success.

        Returns:
            True if this is a Success, False otherwise
        """
        if isinstance(self._value, BaseException):
            return False

        return True

    def is_failure(self) -> bool:
        """
        Check if this Result is a Failure.

        Returns:
            True if this is a Failure, False otherwise
        """
        return not self.is_success()

    def __pow__[B](
        self,
        wrapped_funcs: Applicative[Result[Any, E], Callable[[A], B]],
    ) -> Result[B, E]:
        """
        Infix operator for applicative application.

        This enables the use of ** operator for applying functions in the context of Result.

        Args:
            wrapped_funcs: Result containing a function to apply

        Returns:
            Result[B, E]: Result of applying the function to this value
        """
        return self.ap(wrapped_funcs)

    def __or__[B](
        self,
        f: Callable[[A], Monad[Result[Any, E], B]],
    ) -> Result[B, E]:
        """
        Infix operator for bind.

        Args:
            f: A function that takes a value of type A and returns a Result of type B.

        Returns:
            Result[B, E]: Result of applying the function to this value
        """
        return self.bind(f)

    def __repr__(self) -> str:
        """
        String representation of the Result.

        Returns:
            str: String representation of the Result
        """
        if self.is_success():
            return f"Success({self._value!r})"
        else:
            return f"Failure({self._value!r})"
