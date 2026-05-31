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
    """Optional value monad for type-safe null handling.

    ``Maybe`` encapsulates a value that may or may not be present, eliminating
    ``None`` checks through functional composition. It implements the
    :class:`~katharos.algebra.Monad`, :class:`~katharos.algebra.Applicative`,
    and :class:`~katharos.algebra.Functor` interfaces.

    A ``Maybe`` is in one of two states:

    - **Just**: contains a value of type ``A``.
    - **Nothing**: contains no value.

    Use :meth:`Just` and :meth:`Nothing` to construct values. Use
    :meth:`is_just` and :meth:`is_nothing` to check the state rather than
    ``isinstance`` checks.

    Examples:
        >>> Maybe.Just(5).fmap(lambda x: x * 2)
        Just(10)

        >>> Maybe.Nothing().fmap(lambda x: x * 2)
        Nothing()

        >>> Maybe.Just(3) | (lambda x: Maybe.Just(x + 1))
        Just(4)

    Note:
        This class is ``@final`` and cannot be subclassed. Supports the ``|``
        (bind) and ``**`` (applicative apply) operators.
    """

    @classmethod
    def pure[T](cls: type[Maybe], x: T) -> Maybe[T]:
        """Wrap a value in a Just.

        Args:
            x: The value to wrap.

        Returns:
            A Maybe containing the given value.
        """
        return Maybe.Just(x)

    @classmethod
    def ret[T](cls: type[Maybe[T]], x: T) -> Maybe[T]:
        """Wrap a value in a Just.

        Alias for :meth:`pure`, provided to satisfy the Monad interface.

        Args:
            x: The value to wrap.

        Returns:
            A Maybe containing the given value.
        """
        return cls.pure(x)

    @staticmethod
    def Just(value: A) -> Maybe[A]:  # type: ignore
        """Create a Maybe containing a value.

        Args:
            value: The value to wrap. Must not be a ``Nothing`` instance.

        Returns:
            A Maybe containing the given value.

        Raises:
            TypeError: If ``value`` is a ``_Nothing`` instance.
        """
        if is_nothing(value):
            raise TypeError("Value cannot be Nothing")

        return Maybe(value=value)

    @staticmethod
    def Nothing() -> Maybe[A]:
        """Create an empty Maybe.

        Returns:
            An empty Maybe with no value.
        """
        return Maybe(value=nothing)

    def __init__(self, value: A | _Nothing = nothing) -> None:
        """Initialize a Maybe with an optional value.

        Args:
            value: The value to wrap. Defaults to ``nothing``.
        """
        self._value = value

    def unwrap(self) -> A:
        """Extract the wrapped value.

        Returns:
            The value contained in this Maybe.

        Raises:
            ValueError: If this Maybe is Nothing.
        """
        if is_nothing(self._value):
            raise ValueError("Cannot unwrap a Nothing")

        return cast(A, self._value)

    def fmap[B](self, f: Callable[[A], B]) -> Maybe[B]:
        """Map a function over the wrapped value.

        Args:
            f: Function to apply to the value.

        Returns:
            A Maybe containing the mapped value, or Nothing if this is Nothing.
        """
        if is_nothing(self._value):
            return Maybe[B]()

        return Maybe[B](f(self.unwrap()))

    def ap[B](
        self,
        wrapped_funcs: Applicative[Maybe, Callable[[A], B]],
    ) -> Maybe[B]:
        """Apply a function wrapped in a Maybe to this Maybe's value.

        Args:
            wrapped_funcs: A Maybe containing a function to apply.

        Returns:
            A Maybe containing the result, or Nothing if either operand is Nothing.
        """
        wrapped_funcs = cast(Maybe[Callable[[A], B]], wrapped_funcs)

        if is_nothing(self._value) or is_nothing(wrapped_funcs._value):
            return Maybe[B].Nothing()

        return Maybe[B].Just(wrapped_funcs.unwrap()(self.unwrap()))

    def bind[B](
        self,
        f: Callable[[A], Monad[Maybe, B]],
    ) -> Maybe[B]:
        """Chain a function that returns a Maybe.

        Args:
            f: A function that takes the wrapped value and returns a Maybe.

        Returns:
            The result of applying ``f``, or Nothing if this is Nothing.
        """
        f = cast(Callable[[A], Maybe[B]], f)
        if is_nothing(self._value):
            return Maybe[B].Nothing()

        return f(self.unwrap())

    def is_just(self) -> bool:
        """Check if this Maybe contains a value.

        Returns:
            True if this is a Just, False if it is Nothing.
        """
        return not is_nothing(self._value)

    def is_nothing(self) -> bool:
        """Check if this Maybe contains no value.

        Returns:
            True if this is Nothing, False if it is a Just.
        """
        return is_nothing(self._value)

    def __pow__[B](
        self,
        wrapped_funcs: Applicative["Maybe", Callable[[A], B]],
    ) -> Maybe[B]:
        """Infix operator for applicative application (``**``).

        Args:
            wrapped_funcs: A Maybe containing a function to apply.

        Returns:
            A Maybe containing the result of applying the function.
        """
        return self.ap(wrapped_funcs)

    def __or__[B](
        self,
        f: Callable[[A], Monad[Maybe, B]],
    ) -> Maybe[B]:
        """Infix operator for monadic bind (``|``).

        Args:
            f: A function that takes the wrapped value and returns a Maybe.

        Returns:
            The result of applying ``f``, or Nothing if this is Nothing.
        """
        return self.bind(f)

    def __eq__(self, other: object) -> bool:
        """Check equality with another Maybe.

        Args:
            other: The object to compare with.

        Returns:
            True if both are the same state and hold equal values.
        """
        if not isinstance(other, Maybe):
            return False

        return self._value == other._value

    def __repr__(self) -> str:
        """Return the string representation of this Maybe.

        Returns:
            ``Just(<value>)`` or ``Nothing()``.
        """
        return f"Just({self._value!r})" if self.is_just() else "Nothing()"

    def __hash__(self) -> int:
        """Return a hash of this Maybe.

        Returns:
            Hash of the wrapped value, or a constant for Nothing.
        """
        return hash(self._value)
