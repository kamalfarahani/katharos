from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar, cast, final

from katharos.algebra.applicative.applicative import Applicative
from katharos.algebra.monad import Monad

A = TypeVar("A", covariant=True)


@final
class _Nothing:
    """
    Singleton class representing an empty Maybe.
    """

    def __eq__(self, value: object, /) -> bool:
        if not isinstance(value, _Nothing):
            return False
        return True

    def __repr__(self) -> str:
        return "Nothing()"

    def __hash__(self) -> int:
        return hash("Nothing")

    def __bool__(self) -> bool:
        return False


nothing = _Nothing()


def is_nothing(value: Any) -> bool:
    return isinstance(value, _Nothing)


@final
class Maybe(Monad["Maybe[Any]", A]):
    """
    A Maybe monad representing an optional value.

    The Maybe type encapsulates a value that may or may not be present, providing
    a type-safe way to handle optional values without using None checks. It implements
    the Monad, Applicative, and Functor interfaces.

    A Maybe can be in one of two states:
    - Just(value): Contains a value
    - Nothing(): Contains no value (value is None)

    Examples:
        >>> just_value = Maybe.Just(5)
        >>> just_value.fmap(lambda x: x * 2)
        Just(10)

        >>> nothing = Maybe.Nothing()
        >>> nothing.fmap(lambda x: x * 2)
        Nothing()

        >>> Maybe.Just(3) | (lambda x: Maybe.Just(x + 1))
        Just(4)

    Note:
        This class is marked as @final and cannot be subclassed. Use `is_just()`
        and `is_nothing()` methods to check the state. Use `Maybe.Just()` to create
        a Maybe with a value and `Maybe.Nothing()` to create an empty Maybe.
        The class supports the following operators:
        - `|` (pipe): Monadic bind operation
        - `**` (power): Applicative application
    """

    @classmethod
    def pure[T](cls: type[Maybe], x: T) -> Maybe[T]:
        """
        Return a Maybe containing the given value.

        Args:
            x: The value to wrap in a Maybe.

        Returns:
            Maybe[A]: A Maybe containing the given value.
        """
        return Maybe.Just(x)

    @classmethod
    def ret[T](cls: type[Maybe[T]], x: T) -> Maybe[T]:
        """
        Return a Maybe containing the given value.

        Args:
            x: The value to wrap in a Maybe.

        Returns:
            Maybe[A]: A Maybe containing the given value.
        """
        return cls.pure(x)

    @staticmethod
    def Just(value: A) -> Maybe[A]:  # type: ignore
        """
        Create a Maybe containing a value.

        Args:
            value: The value to wrap in a Maybe. Must not be Nothing.

        Returns:
            Maybe[A]: A Maybe containing the given value.

        Raises:
            TypeError: If the value is of type _Nothing.
        """
        if is_nothing(value):
            raise TypeError("Value cannot be Nothing")

        return Maybe(value=value)

    @staticmethod
    def Nothing() -> Maybe[A]:
        """
        Create an empty Maybe.

        Returns:
            Maybe[A]: An empty Maybe.
        """
        return Maybe(value=nothing)

    def __init__(self, value: A | _Nothing = nothing) -> None:
        """
        Initialize a Maybe with an optional value.

        Args:
            value: The optional value to wrap. Defaults to nothing.
        """
        self._value = value

    def unwrap(self) -> A:
        """
        Unwrap the value from the Maybe.

        Returns:
            A: The value contained in the Maybe.

        Raises:
            ValueError: If the Maybe is empty.
        """
        if is_nothing(self._value):
            raise ValueError("Cannot unwrap a Nothing")

        return cast(A, self._value)

    def fmap[B](self, f: Callable[[A], B]) -> Maybe[B]:
        """
        Map a function over the value.

        Args:
            f: Function to apply to the value

        Returns:
            Maybe[B]: Maybe containing the mapped value
        """
        if is_nothing(self._value):
            return Maybe[B]()

        return Maybe[B](f(self.unwrap()))

    def ap[B](
        self,
        wrapped_funcs: Applicative[Maybe, Callable[[A], B]],
    ) -> Maybe[B]:
        """
        Apply a function wrapped in a Maybe to the value.

        Args:
            wrapped_funcs: A Maybe containing a function to apply.

        Returns:
            Maybe[B]: The result of applying the function.
        """
        wrapped_funcs = cast(Maybe[Callable[[A], B]], wrapped_funcs)

        if is_nothing(self._value) or is_nothing(wrapped_funcs._value):
            return Maybe[B].Nothing()

        return Maybe[B].Just(wrapped_funcs.unwrap()(self.unwrap()))

    def bind[B](
        self,
        f: Callable[[A], Monad[Maybe, B]],
    ) -> Maybe[B]:
        """
        Bind a function to the value.

        Args:
            f: The function to apply.

        Returns:
            Maybe[B]: The result of applying the function.
        """
        f = cast(Callable[[A], Maybe[B]], f)
        if is_nothing(self._value):
            return Maybe[B].Nothing()

        return f(self.unwrap())

    def is_just(self) -> bool:
        """
        Check if the Maybe contains a value.

        Returns:
            bool: True if the Maybe contains a value, False otherwise.
        """
        return not is_nothing(self._value)

    def is_nothing(self) -> bool:
        """
        Check if the Maybe does not contain a value.

        Returns:
            bool: True if the Maybe does not contain a value, False otherwise.
        """
        return is_nothing(self._value)

    def __pow__[B](
        self,
        wrapped_funcs: Applicative["Maybe", Callable[[A], B]],
    ) -> Maybe[B]:
        """
        Infix operator for applicative application.

        Args:
            wrapped_funcs: A Maybe containing a function to apply.

        Returns:
            Maybe[B]: The result of applying the function to this value.
        """
        return self.ap(wrapped_funcs)

    def __or__[B](
        self,
        f: Callable[[A], Monad[Maybe, B]],
    ) -> Maybe[B]:
        """
        Pipe operator for Maybe monad.

        Args:
            f: A function that takes the value and returns a Maybe[B].

        Returns:
            Maybe[B]: The result of applying the function.
        """
        return self.bind(f)

    def __eq__(self, other: object) -> bool:
        """
        Check equality with another Maybe.

        Args:
            other: The object to compare with.

        Returns:
            bool: True if the Maybe is equal to the other object, False otherwise.
        """
        if not isinstance(other, Maybe):
            return False

        return self._value == other._value

    def __repr__(self) -> str:
        """
        Return a string representation of the Maybe.

        Returns:
            str: "Just(value)" if the Maybe contains a value, "Nothing()" otherwise.
        """
        return f"Just({self._value})" if self.is_just() else "Nothing()"

    def __hash__(self) -> int:
        """
        Return a hash of the Maybe.

        Returns:
            int: The hash of the Maybe.
        """
        return hash(self._value)
