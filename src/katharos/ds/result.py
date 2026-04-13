from __future__ import annotations

from collections.abc import Callable
from typing import Any, Generic, TypeVar, cast, final

from katharos.algebra import Monad
from katharos.algebra.applicative.applicative import Applicative

E = TypeVar("E", bound=BaseException, covariant=True)
A = TypeVar("A", covariant=True)


@final
class Result(
    Generic[E, A],
    Monad["Result[E, Any]", A],
):
    """A Result monad for error handling without exceptions.

    The Result type encapsulates a computation that can either succeed with a value
    of type A or fail with an exception of type E. It implements the Monad, Applicative,
    and Functor interfaces for composable error handling.

    A Result can be in one of two states:

    - Success: Contains a value of type A (non-exception)
    - Failure: Contains an exception of type E

    Type Parameters:
        E: The type of the exception (must be a subclass of BaseException).
        A: The type of the success value.

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

        - ``|`` (pipe): Monadic bind operation.
        - ``**`` (power): Applicative application.
    """

    @classmethod
    def pure[T](cls: type[Result], x: T) -> Result[E, T]:
        """Wrap a value in a Success.

        Args:
            x: The value to wrap.

        Returns:
            Result[E, T]: A Success containing the value.

        Raises:
            TypeError: If the value is an exception.
        """
        if isinstance(x, BaseException):
            raise TypeError("Cannot create a Result with an exception as the value")

        return Result(x)

    @staticmethod
    def Success(x: A) -> Result[E, A]:  # type: ignore
        """Create a Success result.

        Args:
            x: The value to wrap.

        Returns:
            Result[E, A]: A Success result containing the value.
        """
        return Result.pure(x)

    @staticmethod
    def Failure(e: E) -> Result[E, A]:  # type: ignore
        """Create a Failure result.

        Args:
            e: The exception to wrap.

        Returns:
            Result[E, A]: A Failure result containing the exception.

        Raises:
            TypeError: If the value is not an exception.
        """
        if not isinstance(e, BaseException):
            raise TypeError("Cannot create a Result with a non-exception as the value")

        return Result(e)

    def __init__(self, value: A | E) -> None:
        """Initialize the Result.

        Args:
            value: The value to wrap, either A or E.
        """
        self._value = value

    @property
    def value(self) -> A:
        """Get the success value of the Result.

        Returns:
            A: The success value.

        Raises:
            TypeError: If the Result is a Failure.
        """
        if isinstance(self._value, BaseException):
            raise TypeError("Cannot get the value of a Failure")

        return self._value

    @property
    def error(self) -> E:
        """Get the error of the Result.

        Returns:
            E: The exception value.

        Raises:
            TypeError: If the Result is a Success.
        """
        if not isinstance(self._value, BaseException):
            raise TypeError("Cannot get the error of a Success")

        return cast(E, self._value)

    def fmap[B](self, f: Callable[[A], B]) -> Result[E, B]:
        """Map a function over the success value.

        Args:
            f (Callable[[A], B]): Function to apply to the value.

        Returns:
            Result[E, B]: A new Result containing the mapped value, or the
                original Failure unchanged.
        """
        if isinstance(self._value, BaseException):
            casted_self = cast(Result[E, B], self)
            return casted_self

        return Result(f(self._value))

    def ap[B](
        self,
        wrapped_funcs: Applicative[Result[E, Any], Callable[[A], B]],
    ) -> Result[E, B]:
        """Apply a function wrapped in a Result to this Result.

        Args:
            wrapped_funcs (Applicative[Result[E, Any], Callable[[A], B]]): A
                Result containing the function to apply.

        Returns:
            Result[E, B]: The result of applying the wrapped function to this
                value, or the first encountered Failure.
        """
        wrapped_funcs = cast(Result[E, Callable[[A], B]], wrapped_funcs)
        if isinstance(self._value, BaseException):
            result_err = cast(Result[E, B], self)
            return result_err

        if isinstance(wrapped_funcs._value, BaseException):
            result_err = cast(Result[E, B], wrapped_funcs)
            return result_err

        casted_self = cast(A, self._value)
        inner_func = cast(Callable[[A], B], wrapped_funcs._value)

        return Result(inner_func(casted_self))

    def bind[B](
        self,
        f: Callable[[A], Monad[Result[E, Any], B]],
    ) -> Result[E, B]:
        """Bind a function that returns a Result to this Result.

        Args:
            f (Callable[[A], Monad[Result[E, Any], B]]): A function that takes
                a value of type A and returns a Result of type B.

        Returns:
            Result[E, B]: The result of applying the function to the success
                value, or the original Failure unchanged.
        """
        f = cast(Callable[[A], Result[E, B]], f)
        if isinstance(self._value, BaseException):
            return Result[E, B](self._value)  # type: ignore

        return f(self._value)

    def is_success(self) -> bool:
        """Check if this Result is a Success.

        Returns:
            bool: True if this is a Success, False otherwise.
        """
        if isinstance(self._value, BaseException):
            return False

        return True

    def is_failure(self) -> bool:
        """Check if this Result is a Failure.

        Returns:
            bool: True if this is a Failure, False otherwise.
        """
        return not self.is_success()

    def __pow__[B](
        self,
        wrapped_funcs: Applicative[Result[E, Any], Callable[[A], B]],
    ) -> Result[E, B]:
        """Infix operator for applicative application (``**``).

        Args:
            wrapped_funcs (Applicative[Result[E, Any], Callable[[A], B]]): A
                Result containing the function to apply.

        Returns:
            Result[E, B]: The result of applying the wrapped function to this
                value, or the first encountered Failure.
        """
        return self.ap(wrapped_funcs)

    def __or__[B](
        self,
        f: Callable[[A], Monad[Result[E, Any], B]],
    ) -> Result[E, B]:
        """Infix operator for bind (``|``).

        Args:
            f (Callable[[A], Monad[Result[E, Any], B]]): A function that takes
                a value of type A and returns a Result of type B.

        Returns:
            Result[E, B]: The result of applying the function to the success
                value, or the original Failure unchanged.
        """
        return self.bind(f)

    def __repr__(self) -> str:
        """Return the string representation of the Result.

        Returns:
            str: ``Success(<value>)`` or ``Failure(<error>)``.
        """
        if self.is_success():
            return f"Success({self._value!r})"
        else:
            return f"Failure({self._value!r})"

    def __eq__(self, value: object, /) -> bool:
        """Compare two Result objects for equality.

        Args:
            value (object): The object to compare with.

        Returns:
            bool: True if the objects are equal, False otherwise.
        """
        if not isinstance(value, Result):
            return False

        if self.is_success():
            return self.value == value.value
        else:
            return self.error == value.error
