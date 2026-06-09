from __future__ import annotations

import functools
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

    - **Success**: Contains a value of type ``A`` (non-exception)
    - **Failure**: Contains an exception of type ``E``

    **Type Parameters:**

    - ``E``: The type of the exception (must be a subclass of :class:`BaseException`).
    - ``A``: The type of the success value.

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
        This class is marked as ``@final`` and cannot be subclassed. Use
        :meth:`is_success` and :meth:`is_failure` methods to check the state
        instead of type checking. Use :meth:`Success` to create success values
        and :meth:`Failure` to create failure values. Access success values with
        ``.value`` and failure errors with ``.error``.

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

        Examples:
            >>> Result.pure(42)
            Success(42)

            >>> Result.pure("hello")
            Success('hello')

            >>> Result.pure(ValueError("oops"))  # doctest: +SKIP
            Traceback (most recent call last):
                ...
            TypeError: Cannot create a Result with an exception as the value
        """
        if isinstance(x, BaseException):
            raise TypeError("Cannot create a Result with an exception as the value")

        return Result(x)

    @classmethod
    def ret[T](cls: type[Result[E, T]], x: T) -> Result[E, T]:
        """Wrap a value in a Success.

        Alias for :meth:`pure`, provided to satisfy the Monad interface.

        Args:
            x: The value to wrap.

        Returns:
            Result[E, T]: A Success containing the value.

        Raises:
            TypeError: If the value is an exception.

        Examples:
            >>> Result.ret(42)
            Success(42)
        """
        return cls.pure(x)

    @staticmethod
    def Success(x: A) -> Result[E, A]:  # type: ignore
        """Create a Success result.

        Args:
            x: The value to wrap.

        Returns:
            Result[E, A]: A Success result containing the value.

        Examples:
            >>> Result.Success(42)
            Success(42)

            >>> Result.Success([1, 2, 3])
            Success([1, 2, 3])
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

        Examples:
            >>> Result.Failure(ValueError("bad input"))
            Failure(ValueError('bad input'))

            >>> Result.Failure(42)  # doctest: +SKIP
            Traceback (most recent call last):
                ...
            TypeError: Cannot create a Result with a non-exception as the value
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

        Examples:
            >>> Result.Success(42).value
            42

            >>> Result.Failure(ValueError("err")).value  # doctest: +SKIP
            Traceback (most recent call last):
                ...
            TypeError: Cannot get the value of a Failure
        """
        if isinstance(self._value, BaseException):
            raise TypeError("Cannot get the value of a Failure") from self._value

        return self._value

    @property
    def error(self) -> E:
        """Get the error of the Result.

        Returns:
            E: The exception value.

        Raises:
            TypeError: If the Result is a Success.

        Examples:
            >>> Result.Failure(ValueError("err")).error
            ValueError('err')

            >>> Result.Success(42).error  # doctest: +SKIP
            Traceback (most recent call last):
                ...
            TypeError: Cannot get the error of a Success
        """
        if not isinstance(self._value, BaseException):
            raise TypeError("Cannot get the error of a Success")

        return cast(E, self._value)

    def unwrap(self) -> A:
        """Unwrap the success value, raising an error if this is a Failure.

        This method extracts the success value from a Success Result. If the Result
        is a Failure, it raises a TypeError with the original exception as the cause.

        This is equivalent to accessing the ``.value`` property directly.

        Returns:
            A: The success value contained in this Result.

        Raises:
            TypeError: If the Result is a Failure, with the original exception
                as the cause chain.

        Examples:
            >>> success = Result.Success(42)
            >>> success.unwrap()
            42

            >>> failure = Result.Failure(ValueError("error"))
            >>> failure.unwrap()  # doctest: +SKIP
            Traceback (most recent call last):
                ...
            TypeError: Cannot get the value of a Failure
        """
        return self.value

    def fmap[B](self, f: Callable[[A], B]) -> Result[E, B]:
        """Map a function over the success value.

        Args:
            f: Function to apply to the value.

        Returns:
            Result[E, B]: A new Result containing the mapped value, or the
                original Failure unchanged.

        Examples:
            >>> Result.Success(3).fmap(lambda x: x * 2)
            Success(6)

            >>> Result.Failure(ValueError("err")).fmap(lambda x: x * 2)
            Failure(ValueError('err'))

            >>> Result.Success("hi").fmap(str.upper)
            Success('HI')
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
            wrapped_funcs: A Result containing the function to apply.

        Returns:
            Result[E, B]: The result of applying the wrapped function to this
                value, or the first encountered Failure.

        Examples:
            >>> wrapped_fn = Result.Success(lambda x: x + 1)
            >>> Result.Success(5).ap(wrapped_fn)
            Success(6)

            >>> Result.Failure(ValueError("err")).ap(wrapped_fn)
            Failure(ValueError('err'))

            >>> failure_fn = Result.Failure(TypeError("bad fn"))
            >>> Result.Success(5).ap(failure_fn)
            Failure(TypeError('bad fn'))
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
            f: A function that takes a value of type A and returns a Result of
                type B.

        Returns:
            Result[E, B]: The result of applying the function to the success
                value, or the original Failure unchanged.

        Examples:
            >>> Result.Success(5).bind(lambda x: Result.Success(x + 1))
            Success(6)

            >>> Result.Success(5).bind(lambda x: Result.Failure(ValueError("nope")))
            Failure(ValueError('nope'))

            >>> Result.Failure(ValueError("err")).bind(lambda x: Result.Success(x + 1))
            Failure(ValueError('err'))
        """
        f = cast(Callable[[A], Result[E, B]], f)
        if isinstance(self._value, BaseException):
            return Result[E, B](self._value)  # type: ignore

        return f(self._value)

    def is_success(self) -> bool:
        """Check if this Result is a Success.

        Returns:
            bool: True if this is a Success, False otherwise.

        Examples:
            >>> Result.Success(42).is_success()
            True

            >>> Result.Failure(ValueError("err")).is_success()
            False
        """
        if isinstance(self._value, BaseException):
            return False

        return True

    def is_failure(self) -> bool:
        """Check if this Result is a Failure.

        Returns:
            bool: True if this is a Failure, False otherwise.

        Examples:
            >>> Result.Failure(ValueError("err")).is_failure()
            True

            >>> Result.Success(42).is_failure()
            False
        """
        return not self.is_success()

    def __pow__[B](
        self,
        wrapped_funcs: Applicative[Result[E, Any], Callable[[A], B]],
    ) -> Result[E, B]:
        """Infix operator for applicative application (``**``).

        Args:
            wrapped_funcs: A Result containing the function to apply.

        Returns:
            Result[E, B]: The result of applying the wrapped function to this
                value, or the first encountered Failure.

        Examples:
            >>> Result.Success(5) ** Result.Success(lambda x: x + 1)
            Success(6)

            >>> Result.Failure(ValueError("err")) ** Result.Success(lambda x: x + 1)
            Failure(ValueError('err'))
        """
        return self.ap(wrapped_funcs)

    def __or__[B](
        self,
        f: Callable[[A], Monad[Result[E, Any], B]],
    ) -> Result[E, B]:
        """Infix operator for monadic bind (``|``).

        Args:
            f: A function that takes a value of type A and returns a Result of
                type B.

        Returns:
            Result[E, B]: The result of applying the function to the success
                value, or the original Failure unchanged.

        Examples:
            >>> Result.Success(5) | (lambda x: Result.Success(x + 1))
            Success(6)

            >>> (Result.Success(5)
            ...     | (lambda x: Result.Success(x * 2))
            ...     | (lambda x: Result.Success(x - 1)))
            Success(9)

            >>> Result.Failure(ValueError("err")) | (lambda x: Result.Success(x + 1))
            Failure(ValueError('err'))
        """
        return self.bind(f)

    def __repr__(self) -> str:
        """Return the string representation of the Result.

        Returns:
            str: ``Success(<value>)`` or ``Failure(<error>)``.

        Examples:
            >>> repr(Result.Success(42))
            'Success(42)'

            >>> repr(Result.Failure(ValueError("err")))
            "Failure(ValueError('err'))"
        """
        if self.is_success():
            return f"Success({self._value!r})"
        else:
            return f"Failure({self._value!r})"

    def __eq__(self, value: object, /) -> bool:
        """Compare two Result objects for equality.

        Two Results are equal if they are both Success with equal values, or
        both Failure with equal errors. A Result is never equal to a non-Result.

        Args:
            value: The object to compare with.

        Returns:
            bool: True if the objects are equal, False otherwise.

        Examples:
            >>> Result.Success(42) == Result.Success(42)
            True

            >>> Result.Success(42) == Result.Success(43)
            False

            >>> err = ValueError("err")
            >>> Result.Failure(err) == Result.Failure(err)
            True

            >>> Result.Success(42) == 42
            False
        """
        if not isinstance(value, Result):
            return False

        if self.is_success():
            return self.value == value.value
        else:
            return self.error == value.error

    @staticmethod
    def catch[Err: BaseException](ExceptionType: type[Err]):
        """Decorator factory that converts a throwing function into one returning a Result.

        Wraps the decorated function so that any exception of type ``ExceptionType``
        raised during its execution is caught and returned as a ``Failure``, while
        normal return values are wrapped in a ``Success``. All other exception types
        propagate unchanged.

        Args:
            ExceptionType: The exception class to catch. Only instances of this
                exact type (or its subclasses) are intercepted.

        Returns:
            A decorator that transforms ``Callable[P, R]`` into
            ``Callable[P, Result[Err, R]]``.

        Examples:
            Basic usage — catch a ``ValueError``:

            >>> @Result.catch(ValueError)
            ... def parse_int(s: str) -> int:
            ...     return int(s)
            >>> parse_int("42")
            Success(42)
            >>> parse_int("bad")
            Failure(ValueError("invalid literal for int() with base 10: 'bad'"))

            Only the declared exception type is caught; others propagate:

            >>> @Result.catch(ValueError)
            ... def risky(x: int) -> int:
            ...     if x < 0:
            ...         raise TypeError("negative")
            ...     return x
            >>> risky(1)
            Success(1)
            >>> risky(-1)
            Traceback (most recent call last):
                ...
            TypeError: negative

            Can be used with functions that take multiple arguments:

            >>> @Result.catch(ZeroDivisionError)
            ... def divide(a: float, b: float) -> float:
            ...     return a / b
            >>> divide(10.0, 2.0)
            Success(5.0)
            >>> divide(10.0, 0.0)
            Failure(ZeroDivisionError('division by zero'))
        """

        def decorator[**P, R](func: Callable[P, R]) -> Callable[P, Result[Err, R]]:
            @functools.wraps(func)
            def safe_func(*args: P.args, **kwargs: P.kwargs) -> Result[Err, R]:
                try:
                    return Result[Err, R].Success(func(*args, **kwargs))
                except ExceptionType as e:
                    return Result[Err, R].Failure(e)

            return safe_func

        return decorator
