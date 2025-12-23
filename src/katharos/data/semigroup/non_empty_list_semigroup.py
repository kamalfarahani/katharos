from __future__ import annotations

from katharos.data.semigroup.semigroup import Semigroup
from katharos.list.non_empty_list import NonEmptyList


class NonEmptyListSemigroup[T](Semigroup):
    """
    Semigroup instance for NonEmptyList.
    """

    def __init__(self, value: NonEmptyList[T]) -> None:
        """
        Initializes the semigroup with a non-empty list.

        Args:
            value: The non-empty list to initialize the semigroup with.
        """
        self.value: NonEmptyList[T] = value

    def __matmul__(
        self,
        other: NonEmptyListSemigroup[T],
    ) -> NonEmptyListSemigroup[T]:
        """
        Returns the result of the semigroup operation on the two semigroups.

        Args:
            other: The other semigroup to perform the operation with.

        Returns:
            The result of the semigroup operation on the two semigroups.
        """
        return NonEmptyListSemigroup(
            value=self.value + other.value,
        )

    def __repr__(self) -> str:
        """
        Returns a string representation of the semigroup.

        Returns:
            A string representation of the semigroup.
        """
        return f"NonEmptyListSemigroup({self.value})"
