from __future__ import annotations

from typing import TypeVar

from katharos.list.immutable_list import ImmutableList

T = TypeVar("T", covariant=True)


class NonEmptyList(ImmutableList[T]):
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
        super().__init__(elements=[head] + tail)
