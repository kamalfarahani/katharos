from __future__ import annotations

from abc import abstractmethod

from katharos.algebra.semigroup.semigroup import Semigroup


class Monoid[M](Semigroup[M]):
    """
    An abstract base class for monoids.

    A monoid is a semigroup with an identity element.
    """

    @classmethod
    @abstractmethod
    def identity(cls) -> M:
        """
        Return the identity element of the monoid.
        Must satisfy: a @ identity = a and identity @ a = a for all a in the monoid.
        The identity element acts as a neutral element for the monoid operation.

        Returns:
            The identity element of type M.
        """
        raise NotImplementedError()
