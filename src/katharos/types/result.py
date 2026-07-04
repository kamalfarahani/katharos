from __future__ import annotations

import functools
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Generic, Never, TypeVar, cast, final, overload
from warnings import deprecated

from katharos.algebra import Monad
from katharos.algebra.applicative.applicative import Applicative
from katharos.types.errors import UnwrapError

E = TypeVar("E", bound=BaseException, covariant=True)
A = TypeVar("A", covariant=True)


@dataclass
class _ErrorWrapper(Generic[E]):
    err: E


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

    - **Success**: Contains a value of type ``A`` (which may itself be an exception)
    - **Failure**: Contains an exception of type ``E``

    The success/failure distinction is tracked internally rather than by the
    type of the wrapped value, so an exception may be carried as a *success*
    value via :meth:`Success`/:meth:`pure` without being treated as a failure.

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

        Truthiness reflects the state: a Success is always truthy (even
        ``Success(0)``), a Failure is falsy.
    """

    @classmethod
    def pure[T](cls: type[Result], x: T) -> Result[E, T]:
        """Wrap a value in a Success.

        Args:
            x: The value to wrap.

        Returns:
            A Success containing the value.

        Raises:
            TypeError: If the value is an internal error wrapper, which would
                masquerade as a Failure.

        Note:
            The value may itself be an exception; it is still wrapped as a
            Success and is *not* treated as a Failure.

        Examples:
            >>> Result.pure(42)
            Success(42)

            >>> Result.pure("hello")
            Success('hello')

            >>> Result.pure(ValueError("oops"))
            Success(ValueError('oops'))
        """
        if isinstance(x, _ErrorWrapper):
            raise TypeError("Value cannot be an internal error wrapper")

        return Result(x)

    @classmethod
    def ret[T](cls: type[Result[E, T]], x: T) -> Result[E, T]:
        """Wrap a value in a Success.

        Alias for :meth:`pure`, provided to satisfy the Monad interface.

        Args:
            x: The value to wrap.

        Returns:
            A Success containing the value.

        Examples:
            >>> Result.ret(42)
            Success(42)
        """
        return cls.pure(x)

    # Overload 1 only matches unspecialized access (``Result.Success(x)``):
    # a subscripted ``Result[E, T].Success`` is never assignable to
    # ``type[Result[Never, Never]]``, so it falls through to overload 2,
    # which binds both type parameters from the class subscript instead
    # of the argument.
    @overload
    @classmethod
    def Success[S](cls: type[Result[Never, Never]], x: S) -> Result[Never, S]: ...

    @overload
    @classmethod
    def Success[Err: BaseException, T](
        cls: type[Result[Err, T]], x: T
    ) -> Result[Err, T]: ...

    @classmethod
    def Success(cls: type[Result[Any, Any]], x: Any) -> Result[Any, Any]:
        """Create a Success result.

        Args:
            x: The value to wrap.

        Returns:
            A Success result containing the value.

        Examples:
            >>> Result.Success(42)
            Success(42)

            >>> Result.Success([1, 2, 3])
            Success([1, 2, 3])
        """
        return Result.pure(x)

    # Same overload scheme as :meth:`Success`, plus a trap overload in the
    # middle: a bare ``Result.Failure(non_exception)`` fails overload 1 on the
    # BaseException bound, but would otherwise leak into the final overload (an
    # unspecialized ``cls`` types as ``type[Result[Unknown, Unknown]]``, so
    # ``Err`` never gets bound-checked there). The trap catches it first and,
    # via ``@deprecated``, surfaces the message at the *call site* -- wherever
    # ``reportDeprecated`` is enabled.
    # and always as a strike-through in Pylance. Its ``Never`` return is
    # truthful: the implementation raises :class:`TypeError` for a
    # non-exception, so that call genuinely never returns (type checkers then
    # treat any following code as unreachable). The trap is never selected for
    # valid calls.
    @overload
    @classmethod
    def Failure[Err: BaseException](
        cls: type[Result[Never, Never]], e: Err
    ) -> Result[Err, Never]: ...

    @overload
    @classmethod
    @deprecated(
        "Result.Failure() requires a BaseException instance you provided a non-exception value."
        " This will raise a TypeError at runtime.",
    )
    def Failure(cls: type[Result[Never, Never]], e: object) -> Never: ...

    @overload
    @classmethod
    def Failure[Err: BaseException, T](
        cls: type[Result[Err, T]], e: Err
    ) -> Result[Err, T]: ...

    @classmethod
    def Failure(cls: type[Result[Any, Any]], e: Any) -> Result[Any, Any]:
        """Create a Failure result.

        Args:
            e: The exception to wrap.

        Returns:
            A Failure result containing the exception.

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

        return Result(_ErrorWrapper(e))

    def __init__(self, value: A | _ErrorWrapper[E]) -> None:
        """Initialize the Result.

        Args:
            value: The value to wrap, either A or E.
        """
        self._value = value

    @property
    def value(self) -> A:
        """Get the success value of the Result.

        Returns:
            The success value.

        Raises:
            UnwrapError: If the Result is a Failure.

        Examples:
            >>> Result.Success(42).value
            42

            >>> Result.Failure(ValueError("err")).value  # doctest: +SKIP
            Traceback (most recent call last):
                ...
            UnwrapError: Cannot get the value of a Failure
        """
        if isinstance(self._value, _ErrorWrapper):
            raise UnwrapError("Cannot get the value of a Failure") from self._value.err

        return self._value

    @property
    def error(self) -> E:
        """Get the error of the Result.

        Returns:
            The exception value.

        Raises:
            UnwrapError: If the Result is a Success.

        Examples:
            >>> Result.Failure(ValueError("err")).error
            ValueError('err')

            >>> Result.Success(42).error  # doctest: +SKIP
            Traceback (most recent call last):
                ...
            UnwrapError: Cannot get the error of a Success
        """
        if not isinstance(self._value, _ErrorWrapper):
            raise UnwrapError("Cannot get the error of a Success")

        return self._value.err

    def unwrap(self) -> A:
        """Unwrap the success value, raising an error if this is a Failure.

        This method extracts the success value from a Success Result. If the Result
        is a Failure, it raises an UnwrapError with the original exception as the
        cause.

        This is equivalent to accessing the ``.value`` property directly.

        Returns:
            The success value contained in this Result.

        Raises:
            UnwrapError: If the Result is a Failure, with the original exception
                as the cause chain.

        Examples:
            >>> success = Result.Success(42)
            >>> success.unwrap()
            42

            >>> failure = Result.Failure(ValueError("error"))
            >>> failure.unwrap()  # doctest: +SKIP
            Traceback (most recent call last):
                ...
            UnwrapError: Cannot get the value of a Failure
        """
        return self.value

    def fmap[B](self, f: Callable[[A], B]) -> Result[E, B]:
        """Map a function over the success value.

        Args:
            f: Function to apply to the value.

        Returns:
            A new Result containing the mapped value, or the
                original Failure unchanged.

        Examples:
            >>> Result.Success(3).fmap(lambda x: x * 2)
            Success(6)

            >>> Result.Failure(ValueError("err")).fmap(lambda x: x * 2)
            Failure(ValueError('err'))

            >>> Result.Success("hi").fmap(str.upper)
            Success('HI')
        """
        if isinstance(self._value, _ErrorWrapper):
            casted_self = cast(Result[E, B], self)
            return casted_self

        return Result[E, B].pure(f(self._value))

    def ap[BE: BaseException, B](
        self,
        wrapped_funcs: Applicative[Result[BE, Any], Callable[[A], B]],
    ) -> Result[BE | E, B]:
        """Apply a function wrapped in a Result to this Result.

        Args:
            wrapped_funcs: A Result containing the function to apply.

        Returns:
            The result of applying the wrapped function to this
                value. The error type ``BE`` comes from ``wrapped_funcs``, not
                from ``self``. Returns the first encountered Failure if either
                operand is a Failure.

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
        wrapped_funcs = cast(Result[BE, Callable[[A], B]], wrapped_funcs)
        if self.is_failure():
            return cast(Result[E, B], self)

        if wrapped_funcs.is_failure():
            return cast(Result[BE, B], wrapped_funcs)

        inner_func = wrapped_funcs.unwrap()
        return Result.pure(inner_func(self.unwrap()))

    def bind[BE: BaseException, B](
        self,
        f: Callable[[A], Monad[Result[BE, Any], B]],
    ) -> Result[BE | E, B]:
        """Bind a function that returns a Result to this Result.

        Args:
            f: A function that takes a value of type A and returns a
                ``Result[BE, B]``.

        Returns:
            The result of applying ``f`` to the success value.
                The error type ``BE`` comes from ``f``'s return type, not from
                ``self``. If ``self`` is a Failure, it is returned unchanged
                (re-typed as ``Result[BE, B]``).

        Examples:
            >>> Result.Success(5).bind(lambda x: Result.Success(x + 1))
            Success(6)

            >>> Result.Success(5).bind(lambda x: Result.Failure(ValueError("nope")))
            Failure(ValueError('nope'))

            >>> Result.Failure(ValueError("err")).bind(lambda x: Result.Success(x + 1))
            Failure(ValueError('err'))
        """
        f = cast(Callable[[A], Result[BE, B]], f)
        if isinstance(self._value, _ErrorWrapper):
            casted_self = cast(Result[E, B], self)
            return casted_self

        return f(self._value)

    def is_success(self) -> bool:
        """Check if this Result is a Success.

        Returns:
            True if this is a Success, False otherwise.

        Examples:
            >>> Result.Success(42).is_success()
            True

            >>> Result.Failure(ValueError("err")).is_success()
            False
        """
        if isinstance(self._value, _ErrorWrapper):
            return False

        return True

    def is_failure(self) -> bool:
        """Check if this Result is a Failure.

        Returns:
            True if this is a Failure, False otherwise.

        Examples:
            >>> Result.Failure(ValueError("err")).is_failure()
            True

            >>> Result.Success(42).is_failure()
            False
        """
        return not self.is_success()

    def __pow__[BE: BaseException, B](
        self,
        wrapped_funcs: Applicative[Result[BE, Any], Callable[[A], B]],
    ) -> Result[BE | E, B]:
        """Infix operator for applicative application (``**``).

        Args:
            wrapped_funcs: A Result containing the function to apply.

        Returns:
            The result of applying the wrapped function to this
                value. The error type ``BE`` comes from ``wrapped_funcs``, not
                from ``self``. Returns the first encountered Failure if either
                operand is a Failure.

        Examples:
            >>> Result.Success(5) ** Result.Success(lambda x: x + 1)
            Success(6)

            >>> Result.Failure(ValueError("err")) ** Result.Success(lambda x: x + 1)
            Failure(ValueError('err'))
        """
        return self.ap(wrapped_funcs)

    def __or__[BE: BaseException, B](
        self,
        f: Callable[[A], Monad[Result[BE, Any], B]],
    ) -> Result[BE | E, B]:
        """Infix operator for monadic bind (``|``).

        Args:
            f: A function that takes a value of type A and returns a
                ``Result[BE, B]``.

        Returns:
            The result of applying ``f`` to the success value.
                The error type ``BE`` comes from ``f``'s return type, not from
                ``self``. If ``self`` is a Failure, it is returned unchanged
                (re-typed as ``Result[BE, B]``).

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
            ``Success(<value>)`` or ``Failure(<error>)``.

        Examples:
            >>> repr(Result.Success(42))
            'Success(42)'

            >>> repr(Result.Failure(ValueError("err")))
            "Failure(ValueError('err'))"
        """
        if self.is_success():
            return f"Success({self.value!r})"
        else:
            return f"Failure({self.error!r})"

    def __eq__(self, value: object, /) -> bool:
        """Compare two Result objects for equality.

        Two Results are equal if they are both Success with equal values, or
        both Failure with equal errors. A Success is never equal to a Failure,
        and a Result is never equal to a non-Result.

        Failures compare by their wrapped exception. Note that exceptions use
        identity equality by default, so two distinct exceptions with the same
        message are not considered equal.

        Args:
            value: The object to compare with.

        Returns:
            True if the objects are equal, False otherwise.

        Examples:
            >>> Result.Success(42) == Result.Success(42)
            True

            >>> Result.Success(42) == Result.Success(43)
            False

            >>> err = ValueError("err")
            >>> Result.Failure(err) == Result.Failure(err)
            True

            >>> Result.Success(42) == Result.Failure(ValueError("err"))
            False

            >>> Result.Success(42) == 42
            False
        """
        if not isinstance(value, Result):
            return NotImplemented

        if self.is_success() != value.is_success():
            return False

        if self.is_success():
            return self.value == value.value
        else:
            return self.error == value.error

    def __bool__(self) -> bool:
        """Return the truthiness of this Result.

        Truthiness reflects the state, not the wrapped value: a Success is
        always truthy, even ``Success(0)`` or ``Success(None)``.

        Returns:
            True if this is a Success, False if it is a Failure.

        Examples:
            >>> bool(Result.Success(0))
            True
            >>> bool(Result.Failure(ValueError("err")))
            False
        """
        return self.is_success()

    def __hash__(self) -> int:
        """Return the hash of the Result.

        The hash is derived from the wrapped value (for a Success) or the
        wrapped exception (for a Failure). A Result is only hashable when its
        contents are hashable.

        Returns:
            The hash of the Result.

        Examples:
            >>> hash(Result.Success(42)) == hash(Result.Success(42))
            True
        """
        if self.is_success():
            return hash((True, self.value))

        return hash((False, self.error))

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
            Failure(ZeroDivisionError('float division by zero'))
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
