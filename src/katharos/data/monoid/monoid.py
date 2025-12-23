from __future__ import annotations

from abc import abstractmethod
from typing import TypeVar

from katharos.data.semigroup.semigroup import Semigroup

M = TypeVar(
    name="M",
    bound="Monoid",
)


class Monoid(Semigroup):
    """
    An abstract base class for monoids.

    A monoid is a semigroup with an identity element.
    """

    @staticmethod
    @abstractmethod
    def identity() -> M:
        """
        Return the identity element of the monoid.
        Must satisfy: a @ identity = a and identity @ a = a for all a in the monoid.
        The identity element acts as a neutral element for the monoid operation.

        Returns:
            The identity element of type M.
        """
        raise NotImplementedError()
