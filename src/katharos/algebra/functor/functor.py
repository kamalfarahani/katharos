from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Generic, TypeVar

A = TypeVar("A")
B = TypeVar("B")


class Functor(ABC, Generic[A]):
    """
    A functor is a type that implements the fmap method,
    allowing functions to be mapped over the structure.


    Laws:
    - Identity: fmap(id) = id
    - Composition: fmap(g . f) = fmap(g) . fmap(f)

    Where id is the identity function and . is function composition.
    """

    @abstractmethod
    def fmap(self, f: Callable[[A], B]) -> Functor[B]:
        """
        Map a function over the functor.

        Args:
            f: A function to apply to the functor's contents

        Returns:
            A new functor with the function applied
        """
        raise NotImplementedError()
