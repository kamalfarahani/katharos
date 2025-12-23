from __future__ import annotations

from collections.abc import Callable

from katharos.algebra.applicative.applicative import Applicative
from katharos.algebra.functor.list_functor import ListFunctor


class ListApplicative[A](Applicative[A], ListFunctor):
    """
    An Applicative instance for lists.
    """

    @staticmethod
    def pure(x: A) -> ListApplicative[A]:
        """
        Return an Applicative containing the given value.
        """
        return ListApplicative([x])

    def ap[B](
        self,
        wrapped_funcs: ListApplicative[Callable[[A], B]],
    ) -> ListApplicative[B]:
        """
        Apply wrapped functions to this Applicative's value.

        Args:
            wrapped_funcs: A ListApplicative containing functions from A to B.

        Returns:
            ListApplicative[B]: A ListApplicative containing the results of applying
                each function to each value.
        """
        return ListApplicative([fn(x) for fn in wrapped_funcs.xs for x in self.xs])

    def __repr__(self) -> str:
        return f"ListApplicative({self.xs})"
