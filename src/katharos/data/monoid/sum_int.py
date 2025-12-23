from __future__ import annotations

from katharos.data.monoid.monoid import Monoid


class SumInt(Monoid):
    """
    A monoid for integer addition.

    This implements the monoid structure where the operation is integer addition
    and the identity element is 0.

    Example:
        >>> a = SumInt(5)
        >>> b = SumInt(3)
        >>> result = a @ b
        >>> print(result)
        SumInt(8)

        >>> identity = SumInt.identity()
        >>> c = SumInt(10)
        >>> result = c @ identity
        >>> print(result)
        SumInt(10)
    """

    def __init__(self, value: int):
        """
        Initialize a SumInt with the given integer value.

        Args:
            value: The integer value to wrap
        """
        self.value: int = value

    def __matmul__(self: SumInt, other: SumInt) -> SumInt:
        """
        Combine this SumInt with another SumInt using addition.

        This implements the monoid operation for integer addition.

        Args:
            other: Another SumInt to add

        Returns:
            A new SumInt representing the sum
        """
        return SumInt(self.value + other.value)

    @staticmethod
    def identity() -> SumInt:
        """
        Return the identity element for addition.

        The identity element is 0, since adding 0 to any integer leaves it unchanged.

        Returns:
            SumInt(0)
        """
        return SumInt(0)

    def __repr__(self) -> str:
        """
        Return a string representation of the SumInt.

        Returns:
            A string in the format "SumInt(value)".
        """
        return f"SumInt({self.value})"
