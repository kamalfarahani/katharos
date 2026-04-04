from __future__ import annotations

from katharos.algebra.monoid import Monoid
from katharos.algebra.semigroup import Semigroup

from .maybe import Maybe


class MonoidMaybe[A: Semigroup](Monoid["MonoidMaybe[A]"]):
    @classmethod
    def identity(cls) -> MonoidMaybe[A]:
        """
        Return the identity element of the MonoidMaybe monoid.

        Returns:
            MonoidMaybe[A]: A MonoidMaybe containing Nothing, which acts as the identity.
        """
        return MonoidMaybe(maybe=Maybe[A]())

    def __init__(self, maybe: Maybe[A]) -> None:
        """
        Initialize the MonoidMaybe with a Maybe value.

        Args:
            maybe: The Maybe value to wrap in a MonoidMaybe.
        """
        self._maybe = maybe

    @property
    def maybe(self) -> Maybe[A]:
        """
        Returns the Maybe value.

        Returns:
            Maybe[A]: The Maybe value.
        """
        return self._maybe

    def op(self, other: MonoidMaybe[A]) -> MonoidMaybe[A]:
        """
        Combine this MonoidMaybe with another MonoidMaybe.

        Args:
            other: Another MonoidMaybe to combine with.

        Returns:
            MonoidMaybe[A]: The result of combining the two MonoidMaybes.
        """
        match self.maybe.value, other.maybe.value:
            case None, _:
                return other
            case _, None:
                return self
            case v_1, v_2:
                return MonoidMaybe(maybe=Maybe(value=v_1 @ v_2))
