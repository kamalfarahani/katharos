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
    """A monoid for multiplication, wrapping a numeric or multiplicative-monoid value.

    Use ``Product[int]``, ``Product[float]``, etc. to obtain a specialised
    subclass whose :meth:`identity` returns the correct one element.
    """

    @classmethod
    def __class_getitem__(cls, item: type[S]) -> type["Product"]:
        """Return a dynamic subclass of ``Product`` bound to the given element type.

        Called implicitly by the ``Product[SomeType]`` subscription syntax so
        that :meth:`identity` can instantiate the correct one element.

        Args:
            item: The concrete numeric or multiplicative-monoid type to bind.

        Returns:
            A new subclass of ``Product`` with ``_S_type`` set to ``item``.
        """
        name = f"{cls.__name__}[{item.__name__}]"
        return type(name, (cls,), {"_S_type": item})

    @classmethod
    def identity(cls: type[Product[S]]) -> Product[S]:
        """Return the multiplicative identity (one) for this type.

        Returns:
            A Product wrapping the one element of type S.

        Raises:
            TypeError: If called on the unparameterised ``Product`` class.
        """
        if cls._S_type is None:  # type: ignore
            raise TypeError("You must specify the type, e.g., Product[int].identity()")

        if cls._S_type in (int, float, complex, decimal.Decimal):  # type: ignore
            one_val = cls._S_type(1)  # type: ignore
        else:
            one_val = cls._S_type.one()  # type: ignore

        return cls(one_val)  # type: ignore

    def __init__(self, value: S) -> None:
        """Initialize a Product with a value of type S.

        Args:
            value: The value to wrap.
        """
        self._value = value

    def op(self, other: Product[S]) -> Product[S]:
        """Multiply two Product values.

        Args:
            other: Another Product instance to combine with.

        Returns:
            A new Product containing the product of both wrapped values.
        """
        return Product(self._value * other._value)

    def __repr__(self) -> str:
        """Return the string representation of this Product.

        Returns:
            ``Product(<value>)`` with the wrapped value.
        """
        return f"Product({self._value!r})"
