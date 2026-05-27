from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator


class BaseImmutableList[T](ABC):
    """Abstract base class for immutable list types.

    Provides read-only sequence operations over a fixed internal element list.
    Subclasses must implement :meth:`__eq__`, :meth:`__hash__`, and
    :meth:`__add__`.
    """

    _elements: list[T]

    def __init__(self, elements: Iterable[T]) -> None:
        """Initialize the list with the given elements.

        Args:
            elements: The elements to populate the list with.
        """
        self._elements = list(elements)

    def __len__(self) -> int:
        """Return the number of elements in the list.

        Returns:
            The element count.
        """
        return len(self._elements)

    def __iter__(self) -> Iterator[T]:
        """Return an iterator over the elements in the list.

        Returns:
            An iterator over the elements.
        """
        return iter(self._elements)

    def __getitem__(self, index: int) -> T:
        """Return the element at the given index.

        Args:
            index: The index of the element to return.

        Returns:
            The element at the given index.
        """
        return self._elements[index]

    def __contains__(self, item: object) -> bool:
        """Check whether the list contains the given item.

        Args:
            item: The item to look for.

        Returns:
            True if the item is present, False otherwise.
        """
        return item in self._elements

    def __ne__(self, other: object) -> bool:
        """Check inequality with another object.

        Args:
            other: The object to compare with.

        Returns:
            True if this list is not equal to ``other``.
        """
        return not self == other

    def __str__(self) -> str:
        """Return the string representation of the internal element list.

        Returns:
            The string form of the underlying Python list.
        """
        return str(self._elements)

    @abstractmethod
    def __eq__(self, other: object) -> bool:
        """Check equality with another object.

        Args:
            other: The object to compare with.

        Returns:
            True if this list is equal to ``other``.
        """
        raise NotImplementedError()

    @abstractmethod
    def __hash__(self) -> int:
        """Return a hash of the list contents.

        Returns:
            A hash value for this list.
        """
        raise NotImplementedError()

    @abstractmethod
    def __add__(self, other: Iterable[T]) -> BaseImmutableList:
        """Concatenate this list with another iterable.

        Args:
            other: The iterable to append.

        Returns:
            A new immutable list containing elements from both sequences.
        """
        raise NotImplementedError()
