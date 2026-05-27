from typing import Protocol, Self


class AdditiveMonoid(Protocol):
    """Protocol for types that form an additive monoid.

    An additive monoid has an identity element (zero) and an associative
    addition operation.
    """

    @classmethod
    def zero(cls) -> Self:
        """Return the additive identity element.

        Returns:
            The zero element of the monoid.
        """
        ...

    def __add__(self, other: Self) -> Self:
        """Add another element of the same type.

        Args:
            other: Another element of the same type.

        Returns:
            The sum of this element and ``other``.
        """
        ...
