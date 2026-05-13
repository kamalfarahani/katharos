from __future__ import annotations

import decimal

from katharos.algebra import Monoid

from .multiplicative_monoid import MultiplicativeMonoid


class Product[
    S: (
        MultiplicativeMonoid,
        int,
        float,
        complex,
        decimal.Decimal,
    )
](Monoid["Product[S]"]):
    """
    A monoid for multiplication operations.
    """

    @classmethod
    def __class_getitem__(cls, item: type[S]) -> type["Product"]:
        """
        Intercepts Product[SomeType] and returns a dynamic subclass
        that 'remembers' the type parameter.
        """
        name = f"{cls.__name__}[{item.__name__}]"
        return type(name, (cls,), {"_S_type": item})

    @classmethod
    def identity(cls: type[Product[S]]) -> Product[S]:
        """
        Return the identity element for multiplication.

        Returns:
            The identity element of type S wrapped in Product.
        """
        if cls._S_type is None:  # type: ignore
            raise TypeError("You must specify the type, e.g., Product[int].identity()")

        if cls._S_type in (int, float, complex, decimal.Decimal):  # type: ignore
            one_val = cls._S_type(1)  # type: ignore
        else:
            one_val = cls._S_type.one()  # type: ignore

        return cls(one_val)  # type: ignore

    def __init__(self, value: S) -> None:
        """
        Initialize a Product with a value of type S.

        Args:
            value: The value of type S to wrap.
        """
        self._value = value

    def op(self, other: Product[S]) -> Product[S]:
        """
        Combine two Product values by multiplying their values.

        Args:
            other: Another Product instance to combine with.

        Returns:
            Product[S]: A new Product containing the product of both values of type S.
        """
        return Product(self._value * other._value)

    def __repr__(self) -> str:
        """
        Return a string representation of the Product.

        Returns:
            str: A string in the format 'Product(value)' where value is of type S.
        """
        return f"Product({self._value!r})"
