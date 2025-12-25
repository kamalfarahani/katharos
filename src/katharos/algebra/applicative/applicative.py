from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Self

from katharos.algebra.functor.functor import Functor


class Applicative[A](Functor[A], ABC):
    """
    An Applicative functor is a functor with additional structure that allows
    for function application within a computational context.

    Applicative functors sit between Functors and Monads in the hierarchy of
    abstractions. They allow you to apply functions wrapped in a context to
    values wrapped in a context.

    Methods:
        pure: Lift a value into the Applicative context.
        ap: Apply a wrapped function to a wrapped value.

    Operators:
        ^: Infix operator for ap (applicative application).

    Laws:
        - Identity: v ^ pure(id) = v
        - Composition: w ^ (v ^ (u ^ pure(compose))) = (w ^ v) ^ u
        - Homomorphism: pure(x) ^ pure(f) = pure(f(x))
        - Interchange: pure(y) ^ u = u ^ pure(lambda f: f(y))

    Where:
        - id is the identity function: lambda x: x
        - compose is function composition: lambda f: lambda g: lambda x: f(g(x))
        - u, v, w are Applicative values containing functions
        - f is a function
        - x, y are plain values
    """

    @staticmethod
    @abstractmethod
    def pure(x: A) -> Self:
        """
        Return an Applicative containing the given value.

        Args:
            x: The value to wrap in an Applicative.

        Returns:
            Applicative[A]: An Applicative containing the given value.
        """
        raise NotImplementedError()

    @abstractmethod
    def ap[B](
        self,
        wrapped_funcs,  # SubclassApplicative[Callable[[A], B]],
    ) -> Applicative[B]:
        """
        Apply wrapped functions to this Applicative's value.

        Args:
            wrapped_funcs: An Applicative containing functions from A to B.

        Returns:
            Applicative[B]: An Applicative containing the result of applying the function.
        """
        raise NotImplementedError()

    def __xor__[B](
        self,
        wrapped_funcs,  # SubclassApplicative[Callable[[A], B]],
    ) -> Applicative[B]:
        """
        Apply wrapped functions to this Applicative's value.

        Args:
            wrapped_funcs: An Applicative containing functions from A to B.

        Returns:
            Applicative[B]: An Applicative containing the result of applying the function.

        """
        return self.ap(wrapped_funcs)
