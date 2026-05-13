from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator


class BaseImmutableList[T](ABC):
    _elements: list[T]

    def __init__(self, elements: Iterable[T]) -> None:
        """
        Initialize the list with the given elements.

        Args:
            elements: The elements to initialize the list with.
        """
        self._elements = list(elements)

    def __len__(self) -> int:
        """
        Return the number of elements in the list.

        Returns:
            int: The number of elements in the list.
        """
        return len(self._elements)

    def __iter__(self) -> Iterator[T]:
        """
        Return an iterator over the elements in the list.

        Returns:
            Iterator[T]: An iterator over the elements in the list.
        """
        return iter(self._elements)

    def __getitem__(self, index: int) -> T:
        """
        Return the element at the given index.

        Args:
            index: The index of the element to return.

        Returns:
            T: The element at the given index.
        """
        return self._elements[index]

    def __contains__(self, item: object) -> bool:
        """
        Return True if the list contains the given item, False otherwise.

        Args:
            item: The item to check for.

        Returns:
            bool: True if the list contains the given item, False otherwise.
        """
        return item in self._elements

    def __ne__(self, other: object) -> bool:
        """
        Return True if the list is not equal to the other object, False otherwise.

        Args:
            other: The object to compare to.

        Returns:
            bool: True if the list is not equal to the other object, False otherwise.
        """
        return not self == other

    def __str__(self) -> str:
        """
        Return a string representation of the list.

        Returns:
            str: A string representation of the list.
        """
        return str(self._elements)

    @abstractmethod
    def __eq__(self, other: object) -> bool:
        """
        Return True if the list is equal to the other object, False otherwise.

        Args:
            other: The object to compare to.

        Returns:
            bool: True if the list is equal to the other object, False otherwise.
        """
        raise NotImplementedError()

    @abstractmethod
    def __hash__(self) -> int:
        """
        Return the hash value of the list.

        Returns:
            int: The hash value of the list.
        """
        raise NotImplementedError()

    @abstractmethod
    def __add__(self, other: Iterable[T]) -> BaseImmutableList:
        """
        Return a new ImmutableList containing the elements of the list and the other iterable.

        Args:
            other: The iterable to add to the list.

        Returns:
            BaseImmutableList[T]: A new ImmutableList containing the elements of the list and the other iterable.
        """
        raise NotImplementedError()
