from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar

S = TypeVar(
    name="S",
    bound="Semigroup",
)


class Semigroup(ABC):
    """
    An abstract base class for semigroups.

    A semigroup is a set equipped with an associative binary operation.
    The binary operation is represented by the @ operator.
    """

    @abstractmethod
    def op(self: S, other: S) -> S:
        """
        Combine this semigroup with another semigroup.

        This is the abstract binary operation that must be implemented by all semigroups.
        Must satisfy the associativity property: (a @ b) @ c = a @ (b @ c)

        Args:
            other: Another semigroup of the same type

        Returns:
            The result of combining the two semigroups
        """

        raise NotImplementedError()

    def __matmul__(self: S, other: S) -> S:
        """
        Combine this semigroup with another semigroup.
        Must satisfy the associativity property: (a @ b) @ c = a @ (b @ c)

        Args:
            other: Another semigroup of the same type

        Returns:
            A new semigroup representing the combination
        """
        return self.op(other)
