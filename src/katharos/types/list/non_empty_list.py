from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any, TypeVar  # noqa: F401

from katharos.algebra import Monad, Semigroup
from katharos.algebra.applicative.applicative import Applicative

from .base_immutable_list import BaseImmutableList

T = TypeVar(name="T", covariant=True)


class NonEmptyList(
    BaseImmutableList[T],
    Monad["NonEmptyList[Any]", T],
    Semigroup["NonEmptyList[T]"],
):
    """An immutable list guaranteed to contain at least one element.

    ``NonEmptyList`` provides the same functional interface as
    :class:`~katharos.types.list.ImmutableList` - including
    :class:`~katharos.algebra.Monad` and
    :class:`~katharos.algebra.semigroup.Semigroup` - without a
    :class:`~katharos.algebra.Monoid` instance (no empty list is representable).

    Access the first element with :attr:`head` and the remaining elements
    with :attr:`tail`.
    """

    def __init__(
        self,
        head: T,
        tail: list[T],
    ) -> None:
        """Create a non-empty list with at least one element.

        Args:
            head: The first (guaranteed) element.
            tail: The remaining elements (may be empty).
        """
        elements: list[T] = [head] + tail
        super().__init__(elements)

    def __eq__(self, other: object) -> bool:
        """Check equality with another NonEmptyList.

        Args:
            other: The object to compare with.

        Returns:
            True if ``other`` is a NonEmptyList with identical elements.
        """
        if not isinstance(other, NonEmptyList):
            return False
        return self._elements == other._elements

    def __hash__(self) -> int:
        """Return a hash of the list contents.

        Returns:
            Hash of the element tuple.
        """
        return hash(tuple(self._elements))

    def __add__(self, other: Iterable[T]) -> NonEmptyList[T]:
        """Concatenate this list with another iterable.

        Args:
            other: The elements to append.

        Returns:
            A new NonEmptyList containing all elements from both sequences.
        """
        head = self.head
        tail = self._elements[1:] + list(other)

        return NonEmptyList(head, tail)

    def __repr__(self) -> str:
        """Return a string representation of this list.

        Returns:
            ``NonEmptyList([...])`` with the element list.
        """
        return f"NonEmptyList({self._elements!r})"

    @property
    def head(self) -> T:
        """The first element of the list.

        Returns:
            The first element.
        """
        return self._elements[0]

    @property
    def tail(self) -> list[T]:
        """All elements after the first.

        Returns:
            A plain list of the remaining elements (may be empty).
        """
        return self._elements[1:]

    @classmethod
    def pure[A](cls: type[NonEmptyList], x: A) -> NonEmptyList[A]:
        """Wrap a single value in a NonEmptyList.

        Args:
            x: The element to wrap.

        Returns:
            A singleton NonEmptyList containing only ``x``.
        """

        return NonEmptyList(head=x, tail=[])

    @classmethod
    def ret[A](cls: type[NonEmptyList[A]], x: A) -> NonEmptyList[A]:
        """Wrap a single value in a NonEmptyList.

        Alias for :meth:`pure`, provided to satisfy the Monad interface.

        Args:
            x: The element to wrap.

        Returns:
            A singleton NonEmptyList containing only ``x``.
        """

        return cls.pure(x)

    def fmap[B](self, f: Callable[[T], B]) -> NonEmptyList[B]:
        """Map a function over every element.

        Args:
            f: A function to apply to each element.

        Returns:
            A new NonEmptyList with the function applied to each element.
        """

        return NonEmptyList(
            head=f(self.head),
            tail=list(map(f, self.tail)),
        )

    def ap[B](
        self,
        wrapped_funcs: Applicative[NonEmptyList, Callable[[T], B]],
    ) -> NonEmptyList[B]:
        """Apply each wrapped function to each element (cartesian product).

        Args:
            wrapped_funcs: A NonEmptyList of functions to apply.

        Returns:
            A new NonEmptyList with results of applying every function to
            every element.
        """
        assert isinstance(wrapped_funcs, NonEmptyList), (
            "wrapped_funcs must be a NonEmptyList of functions"
        )

        applied: list[B] = [f(x) for f in wrapped_funcs for x in self]
        return NonEmptyList(
            head=applied[0],
            tail=applied[1:],
        )

    def bind[B](
        self,
        f: Callable[[T], Monad[NonEmptyList, B]],
    ) -> NonEmptyList[B]:
        """Flatmap this list with a function that returns a NonEmptyList (concatMap).

        Args:
            f: A function that takes an element and returns a NonEmptyList.

        Returns:
            A new NonEmptyList with the results of all returned lists
            concatenated.
        """
        result = []
        for x in self._elements:
            nested = f(x)
            assert isinstance(nested, NonEmptyList), "f must return a NonEmptyList"
            result.extend(nested)

        return NonEmptyList(head=result[0], tail=result[1:])

    def op(self, other: NonEmptyList[T]) -> NonEmptyList[T]:
        """Concatenate this list with another NonEmptyList.

        Args:
            other: Another NonEmptyList to combine with.

        Returns:
            A new NonEmptyList containing all elements from both lists.
        """
        return self + other
