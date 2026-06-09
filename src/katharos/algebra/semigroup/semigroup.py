from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

S = TypeVar("S", bound="Semigroup[Any]", covariant=True)


class Semigroup(ABC, Generic[S]):
    """Abstract base class for semigroups.

    A semigroup is a set equipped with an associative binary operation.
    The binary operation is represented by the ``@`` operator.
    """

    @abstractmethod
    def op(self, other: S) -> S:  # type: ignore
        """Combine this semigroup with another semigroup.

        The abstract binary operation that subclasses must implement.
        Must satisfy associativity: ``(a @ b) @ c == a @ (b @ c)``.

        Args:
            other: Another semigroup of the same type.

        Returns:
            The result of combining the two semigroups.
        """

        raise NotImplementedError()

    def __matmul__(self, other: S) -> S:  # type: ignore
        """Infix operator for the semigroup binary operation (``@``).

        Must satisfy associativity: ``(a @ b) @ c == a @ (b @ c)``.

        Args:
            other: Another semigroup of the same type.

        Returns:
            A new semigroup representing the combination.
        """
        return self.op(other)
