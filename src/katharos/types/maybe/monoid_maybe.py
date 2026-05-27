from __future__ import annotations

from katharos.algebra.monoid import Monoid
from katharos.algebra.semigroup import Semigroup

from .maybe import Maybe


class MonoidMaybe[A: Semigroup](Monoid["MonoidMaybe[A]"]):
    """A :class:`~katharos.algebra.Monoid` instance for optional semigroup values.

    Lifts a semigroup ``A`` into an optional context: two ``Just`` values are
    combined using their semigroup ``@`` operation; ``Nothing`` acts as the
    identity element, leaving the other operand unchanged.
    """

    @classmethod
    def identity(cls) -> MonoidMaybe[A]:
        """Return the identity element of the MonoidMaybe monoid.

        Returns:
            A MonoidMaybe wrapping Nothing, which acts as the identity.
        """
        return MonoidMaybe(maybe=Maybe[A]())

    def __init__(self, maybe: Maybe[A]) -> None:
        """Initialize the MonoidMaybe with a Maybe value.

        Args:
            maybe: The Maybe value to wrap.
        """
        self._maybe = maybe

    @property
    def maybe(self) -> Maybe[A]:
        """The wrapped Maybe value.

        Returns:
            The Maybe value held by this MonoidMaybe.
        """
        return self._maybe

    def op(self, other: MonoidMaybe[A]) -> MonoidMaybe[A]:
        """Combine this MonoidMaybe with another using the semigroup operation.

        Args:
            other: Another MonoidMaybe to combine with.

        Returns:
            The other operand if this is Nothing; this operand if other is
            Nothing; otherwise a MonoidMaybe wrapping ``Just(self @ other)``.
        """
        match self.maybe.is_just(), other.maybe.is_just():
            case False, _:
                return other
            case _, False:
                return self
            case True, True:
                x_1 = self.maybe.unwrap()
                x_2 = other.maybe.unwrap()
                return MonoidMaybe(maybe=Maybe.Just(value=x_1 @ x_2))
