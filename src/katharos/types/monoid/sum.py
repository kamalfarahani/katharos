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
    """A monoid for addition, wrapping a numeric or additive-monoid value.

    Use ``Sum[int]``, ``Sum[float]``, etc. to obtain a specialised subclass
    whose :meth:`identity` returns the correct zero element.
    """

    @classmethod
    def __class_getitem__(cls, item: type[S]) -> type["Sum"]:
        """Return a dynamic subclass of ``Sum`` bound to the given element type.

        Called implicitly by the ``Sum[SomeType]`` subscription syntax so that
        :meth:`identity` can instantiate the correct zero element.

        Args:
            item: The concrete numeric or additive-monoid type to bind.

        Returns:
            A new subclass of ``Sum`` with ``_S_type`` set to ``item``.
        """
        name = f"{cls.__name__}[{item.__name__}]"
        return type(name, (cls,), {"_S_type": item})

    @classmethod
    def identity(cls: type[Sum[S]]) -> Sum[S]:
        """Return the additive identity (zero) for this type.

        Returns:
            A Sum wrapping the zero element of type S.

        Raises:
            TypeError: If called on the unparameterised ``Sum`` class.
        """
        if cls._S_type is None:  # type: ignore
            raise TypeError("You must specify the type, e.g., Sum[int].identity()")

        if cls._S_type in (int, float, complex, decimal.Decimal):  # type: ignore
            zero_val = cls._S_type(0)  # type: ignore
        else:
            zero_val = cls._S_type.zero()  # type: ignore

        return cls(zero_val)  # type: ignore

    def __init__(self, value: S) -> None:
        """Initialize a Sum with a value of type S.

        Args:
            value: The value to wrap.
        """
        self._value = value

    def op(self, other: Sum[S]) -> Sum[S]:
        """Add two Sum values.

        Args:
            other: Another Sum instance to combine with.

        Returns:
            A new Sum containing the sum of both wrapped values.
        """
        return Sum(self._value + other._value)

    def __repr__(self) -> str:
        """Return the string representation of this Sum.

        Returns:
            ``Sum(<value>)`` with the wrapped value.
        """
        return f"Sum({self._value!r})"
