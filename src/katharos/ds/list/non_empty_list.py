from __future__ import annotations

from collections.abc import Iterable
from typing import TypeVar

from .base_immutable_list import BaseImmutableList

T = TypeVar(name="T", covariant=True)


class NonEmptyList(BaseImmutableList[T]):
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
        if not isinstance(other, NonEmptyList):
            return False
        return self._elements == other._elements

    def __hash__(self) -> int:
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
