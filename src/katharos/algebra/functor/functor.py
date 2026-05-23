from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable


class Functor[F, A](ABC):
    """Abstract base class for functors.

    A functor is a type that implements :meth:`fmap`, allowing functions to be
    mapped over the structure.

    Note:
        Instances must satisfy the functor laws:

        - **Identity**: ``fmap(id) == id``
        - **Composition**: ``fmap(g ∘ f) == fmap(g) ∘ fmap(f)``
    """

    @abstractmethod
    def fmap[B](self, f: Callable[[A], B]) -> Functor[F, B]:
        """Map a function over the functor.

        Args:
            f: A function to apply to the functor's contents.

        Returns:
            A new functor with the function applied.
        """
        raise NotImplementedError()
