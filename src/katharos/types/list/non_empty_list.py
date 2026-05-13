from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any, TypeVar

from katharos.algebra import Monad, Semigroup
from katharos.algebra.applicative.applicative import Applicative

from .base_immutable_list import BaseImmutableList

T = TypeVar(name="T", covariant=True)


class NonEmptyList(
    BaseImmutableList[T],
    Monad["NonEmptyList[Any]", T],
    Semigroup["NonEmptyList[T]"],
):
    """
    A non-empty list implementation.
    """

    def __init__(
        self,
        head: T,
        tail: list[T],
    ) -> None:
        """
        Create a non-empty list with at least one element.

        Args:
            head: The first element of the list.
            tail: The remaining elements of the list.
        """
        elements: list[T] = [head] + tail
        super().__init__(elements)

    def __eq__(self, other: object) -> bool:
        """
        Returns true if the other object is equal to this list.

        Args:
            other: The object to compare to this list.

        Returns:
            bool: True if the other object is equal to this list.
        """
        if not isinstance(other, NonEmptyList):
            return False
        return self._elements == other._elements

    def __hash__(self) -> int:
        """
        Returns the hash value of the list.

        Returns:
            int: The hash value of the list.
        """
        return hash(tuple(self._elements))

    def __add__(self, other: Iterable[T]) -> NonEmptyList[T]:
        """
        Concatenate two non-empty lists.

        Args:
            other: The list to concatenate to the list.

        Returns:
            NonEmptyList[T]: The concatenated list.
        """
        head = self.head
        tail = self._elements[1:] + list(other)

        return NonEmptyList(head, tail)

    def __repr__(self) -> str:
        """
        Returns a string representation of the list.

        Returns:
            str: A string representation of the list.
        """
        return f"NonEmptyList({self._elements!r})"

    @property
    def head(self) -> T:
        """
        Return the head of the list.

        Returns:
            T: The head of the list.
        """
        return self._elements[0]

    @property
    def tail(self) -> list[T]:
        """
        Return the tail of the list.

        Returns:
            list[T]: The tail of the list.
        """
        return self._elements[1:]

    @classmethod
    def pure[A](cls: type[NonEmptyList], x: A) -> NonEmptyList[A]:
        """Return a singleton NonEmptyList containing the given element.

        Args:
            x: The element to wrap in a NonEmptyList.

        Returns:
            NonEmptyList[A]: A NonEmptyList containing only the given element.
        """

        return NonEmptyList(head=x, tail=[])

    def fmap[B](self, f: Callable[[T], B]) -> NonEmptyList[B]:
        """Map a function over the elements of this NonEmptyList.

        Args:
            f: A function to apply to each element.

        Returns:
            NonEmptyList[B]: A new NonEmptyList with the function applied to each element.
        """

        return NonEmptyList(
            head=f(self.head),
            tail=list(map(f, self.tail)),
        )

    def ap[B](
        self,
        wrapped_funcs: Applicative[NonEmptyList, Callable[[T], B]],
    ) -> NonEmptyList[B]:
        """Apply functions in this NonEmptyList to values in another NonEmptyList.

        Args:
            wrapped_funcs: A NonEmptyList of functions to apply.

        Returns:
            NonEmptyList[B]: A new NonEmptyList with results of applying the functions.
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
        """Bind (flatMap) this NonEmptyList with a function that returns another NonEmptyList.

        Args:
            f: A function that takes an element and returns a NonEmptyList.

        Returns:
            NonEmptyList[B]: A new NonEmptyList with the results of applying the function.
        """
        result = []
        for x in self._elements:
            nested = f(x)
            assert isinstance(nested, NonEmptyList), "f must return a NonEmptyList"
            result.extend(nested)

        return NonEmptyList(head=result[0], tail=result[1:])

    def op(self, other: NonEmptyList[T]) -> NonEmptyList[T]:
        """
        Combine this NonEmptyList with another NonEmptyList.

        Args:
            other: Another NonEmptyList to combine with.

        Returns:
            NonEmptyList[T]: The concatenated list.
        """
        return self + other
