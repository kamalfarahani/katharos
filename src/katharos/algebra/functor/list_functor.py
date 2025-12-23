from __future__ import annotations

from collections.abc import Callable

from katharos.algebra.functor.functor import Functor


class ListFunctor[A](Functor[A]):
    """
    List functor that applies a function to each element of a list.
    """

    xs: list[A]

    def __init__(self, xs: list[A]) -> None:
        self.xs = xs

    def fmap[B](self, f: Callable[[A], B]) -> ListFunctor[B]:
        return ListFunctor([f(x) for x in self.xs])

    def __repr__(self) -> str:
        return f"ListFunctor({self.xs})"
