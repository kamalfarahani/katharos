from __future__ import annotations

from abc import abstractmethod

from katharos.algebra.semigroup.semigroup import Semigroup


class Monoid[M](Semigroup[M]):
    """Abstract base class for monoids.

    A monoid is a semigroup with an identity element.
    """

    @classmethod
    @abstractmethod
    def identity(cls) -> M:
        """Return the identity element of the monoid.

        Must satisfy: ``a @ identity() == a`` and ``identity() @ a == a``
        for all ``a`` in the monoid.

        Returns:
            The identity element of type M.
        """
        raise NotImplementedError()
