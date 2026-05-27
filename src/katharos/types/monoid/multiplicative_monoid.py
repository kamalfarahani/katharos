from typing import Protocol, Self


class MultiplicativeMonoid(Protocol):
    """Protocol for types that form a multiplicative monoid.

    A multiplicative monoid has an identity element (one) and an associative
    multiplication operation.
    """

    @classmethod
    def one(cls) -> Self:
        """Return the multiplicative identity element.

        Returns:
            The one element of the monoid.
        """
        ...

    def __mul__(self, other: Self) -> Self:
        """Multiply this element with another.

        Args:
            other: Another element of the same type.

        Returns:
            The product of this element and ``other``.
        """
        ...
