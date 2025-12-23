from __future__ import annotations

from katharos.data.monoid.monoid import Monoid


class MultInt(Monoid):
    """
    A monoid for integer multiplication.

    This implements the monoid structure where the operation is integer multiplication
    and the identity element is 1.

    Example:
        >>> a = MultInt(5)
        >>> b = MultInt(3)
        >>> result = a @ b
        >>> print(result)
        MultInt(15)

        >>> identity = MultInt.identity()
        >>> c = MultInt(10)
        >>> result = c @ identity
        >>> print(result)
        MultInt(10)
    """

    def __init__(self, value: int):
        """
        Initialize a MultInt with the given integer value.

        Args:
            value: The integer value to wrap
        """
        self.value: int = value

    def __matmul__(self: MultInt, other: MultInt) -> MultInt:
        """
        Combine this MultInt with another MultInt using multiplication.

        This implements the monoid operation for integer multiplication.

        Args:
            other: Another MultInt to multiply

        Returns:
            A new MultInt representing the product
        """
        return MultInt(self.value * other.value)

    @staticmethod
    def identity() -> MultInt:
        """
        Return the identity element for multiplication.

        The identity element is 1, since multiplying any integer by 1 leaves it unchanged.

        Returns:
            MultInt(1)
        """
        return MultInt(1)

    def __repr__(self) -> str:
        """
        Return a string representation of the MultInt.

        Returns:
            A string in the format "MultInt(value)".
        """
        return f"MultInt({self.value})"
