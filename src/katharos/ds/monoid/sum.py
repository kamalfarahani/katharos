from __future__ import annotations

import decimal

from katharos.algebra import Monoid

from .additive_monoid import AdditiveMonoid


class Sum[
    S: (
        AdditiveMonoid,
        int,
        float,
        complex,
        decimal.Decimal,
    )
](Monoid["Sum[S]"]):
    """
    A monoid for addition operations.

    This class wraps a value of type S and provides monoid operations
    for addition.
    """

    @classmethod
    def __class_getitem__(cls, item: type[S]) -> type["Sum"]:
        """
        Intercepts Sum[SomeType] and returns a dynamic subclass
        that 'remembers' the type parameter.
        """
        name = f"{cls.__name__}[{item.__name__}]"
        return type(name, (cls,), {"_S_type": item})

    @classmethod
    def identity(cls: type[Sum[S]]) -> Sum[S]:
        """
        Return the identity element for addition.

        Returns:
            The zero element of type S wrapped in Sum.
        """
        if cls._S_type is None:  # type: ignore
            raise TypeError("You must specify the type, e.g., Sum[int].identity()")

        if cls._S_type in (int, float, complex, decimal.Decimal):  # type: ignore
            zero_val = cls._S_type(0)  # type: ignore
        else:
            zero_val = cls._S_type.zero()  # type: ignore

        return cls(zero_val)  # type: ignore

    def __init__(self, value: S) -> None:
        """
        Initialize a Sum with a value of type S.

        Args:
            value: The value of type S to wrap.
        """
        self._value = value

    def op(self, other: Sum[S]) -> Sum[S]:
        """
        Combine two Sum values by adding their values.

        Args:
            other: Another Sum instance to combine with.

        Returns:
            Sum[S]: A new Sum containing the sum of both values of type S.
        """
        return Sum(self._value + other._value)

    def __repr__(self) -> str:
        """
        Return a string representation of the Sum.

        Returns:
            str: A string in the format 'Sum(value)' where value is of type S.
        """
        return f"Sum({self._value!r})"
