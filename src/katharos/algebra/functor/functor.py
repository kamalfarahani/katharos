from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, Generic, TypeVar

F = TypeVar("F", bound="Functor[Any, Any]", covariant=True)
A = TypeVar("A", covariant=True)


class Functor(ABC, Generic[F, A]):
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
