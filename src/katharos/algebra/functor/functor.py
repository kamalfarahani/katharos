from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable


class Functor[F, A](ABC):
    """
    A functor is a type that implements the fmap method,
    allowing functions to be mapped over the structure.


    Laws:
    - Identity: fmap(id) = id
    - Composition: fmap(g . f) = fmap(g) . fmap(f)

    Where id is the identity function and . is function composition.
    """

    @abstractmethod
    def fmap[B](self, f: Callable[[A], B]) -> Functor[F, B]:
        """
        Map a function over the functor.

        Args:
            f: A function to apply to the functor's contents

        Returns:
            A new functor with the function applied
        """
        raise NotImplementedError()
