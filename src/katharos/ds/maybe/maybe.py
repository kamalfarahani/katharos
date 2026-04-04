from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar, cast, final

from katharos.algebra.applicative.applicative import Applicative
from katharos.algebra.monad import Monad

A = TypeVar("A", covariant=True)


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

    Args:
        value: The optional value to wrap. Defaults to None.

    Examples:
        >>> just_value = Maybe(5)
        >>> just_value.fmap(lambda x: x * 2)
        Just(10)

        >>> nothing = Maybe()
        >>> nothing.fmap(lambda x: x * 2)
        Nothing()

        >>> Maybe(3) | (lambda x: Maybe(x + 1))
        Just(4)
    """

    def __init__(self, value: A | None = None) -> None:
        """
        Initialize a Maybe with an optional value.

        Args:
            value: The optional value to wrap. Defaults to None.
        """
        self.value = value

    @classmethod
    def pure[T](cls: type[Maybe], x: T) -> Maybe[T]:
        """
        Return a Maybe containing the given value.

        Args:
            x: The value to wrap in a Maybe.

        Returns:
            Maybe[A]: A Maybe containing the given value.
        """
        return Maybe(value=x)

    def fmap[B](self, f: Callable[[A], B]) -> Maybe[B]:
        """
        Map a function over the value.

        Args:
            f: Function to apply to the value

        Returns:
            Maybe[B]: Maybe containing the mapped value
        """
        if self.value is None:
            return Maybe[B]()

        return Maybe[B](f(self.value))

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

        if self.value is None or wrapped_funcs.value is None:
            return Maybe[B]()

        return Maybe[B](wrapped_funcs.value(self.value))

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
        if self.value is None:
            return Maybe[B]()

        return f(self.value)

    def is_just(self) -> bool:
        """
        Check if the Maybe contains a value.

        Returns:
            bool: True if the Maybe contains a value, False otherwise.
        """
        return self.value is not None

    def is_nothing(self) -> bool:
        """
        Check if the Maybe does not contain a value.

        Returns:
            bool: True if the Maybe does not contain a value, False otherwise.
        """
        return self.value is None

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

        return self.value == other.value

    def __repr__(self) -> str:
        """
        Return a string representation of the Maybe.

        Returns:
            str: "Just(value)" if the Maybe contains a value, "Nothing()" otherwise.
        """
        return f"Just({self.value})" if self.value is not None else "Nothing()"

    def __hash__(self) -> int:
        """
        Return a hash of the Maybe.

        Returns:
            int: The hash of the Maybe.
        """
        return hash(self.value)
