from __future__ import annotations

from collections.abc import Iterable
from typing import TypeVar

from katharos.algebra.monoid import Monoid

from .base_immutable_list import BaseImmutableList

T = TypeVar(name="T", covariant=True)


class ImmutableList(BaseImmutableList[T], Monoid):
    """
    A covariant immutable list implementation.

    This class provides an immutable wrapper around a list, ensuring that the
    underlying data cannot be modified after creation. The type parameter T is
    covariant, meaning that ImmutableList[Child] is a subtype of ImmutableList[Parent]
    when Child is a subtype of Parent.

    The immutable nature makes instances hashable and safe to use as dictionary keys
    or in sets. All standard sequence operations are supported for read-only access.

    Args:
        elements: The list of elements to wrap. A copy is not made, so the original
                 list should not be modified after passing it to this constructor.

    Examples:
        >>> numbers = ImmutableList([1, 2, 3, 4, 5])
        >>> len(numbers)
        5
        >>> 3 in numbers
        True
        >>> numbers[1]
        2
        >>> list(numbers)
        [1, 2, 3, 4, 5]
        >>> numbers + [6, 7]
        ImmutableList([1, 2, 3, 4, 5, 6, 7])

        # Covariance example:
        >>> strings: ImmutableList[str] = ImmutableList(["hello", "world"])
        >>> objects: ImmutableList[object] = strings  # Valid due to covariance
    """

    def __eq__(self, other: object) -> bool:
        """
        Return True if the list is equal to the other object, False otherwise.

        Args:
            other: The object to compare to.

        Returns:
            bool: True if the list is equal to the other object, False otherwise.
        """
        if not isinstance(other, ImmutableList):
            return False
        return self._elements == other._elements

    def __hash__(self) -> int:
        return hash(tuple(self._elements))

    def __repr__(self) -> str:
        """
        Return a string representation of the list.

        Returns:
            str: A string representation of the list.
        """
        return f"ImmutableList({self._elements!r})"

    def __str__(self) -> str:
        """
        Return a string representation of the list.

        Returns:
            str: A string representation of the list.
        """
        return str(self._elements)

    def __add__(self, other: Iterable[T]) -> ImmutableList[T]:
        """
        Return a new ImmutableList containing the elements of the list and the other list.

        Args:
            other: The list to add to the list.

        Returns:
            ImmutableList[T]: A new ImmutableList containing the elements of the list and the other list.
        """
        return ImmutableList(list(self) + list(other))

    def op(self, other: ImmutableList[T]) -> ImmutableList[T]:
        return self + other

    @property
    def identity(self) -> ImmutableList[T]:
        return ImmutableList([])
