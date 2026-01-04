from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Self

from katharos.algebra.functor.functor import Functor


class Applicative[App, A](Functor[App, A], ABC):
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
        **: Infix operator for ap (applicative application).

    Laws:
        if App is an Applicative:
            - Identity: v ** App.pure(id) = v
            - Composition: w ** (v ** (u ** App.pure(compose))) = (w ** v) ** u
            - Homomorphism: App.pure(x) ** App.pure(f) = App.pure(f(x))
            - Interchange: App.pure(y) ** u = u ** App.pure(lambda f: f(y))

    Where:
        - id is the identity function: lambda x: x
        - compose is function composition: lambda f: lambda g: lambda x: f(g(x))
        - u, v, w are Applicative values containing functions
        - f is a function
        - x, y are plain values
    """

    @classmethod
    @abstractmethod
    def pure[T](cls: type[Self], x: T) -> Applicative[App, T]:
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
        wrapped_funcs: Applicative[App, Callable[[A], B]],
    ) -> Applicative[App, B]:
        """
        Apply wrapped functions to this Applicative's value.

        Args:
            wrapped_funcs: An Applicative containing functions from A to B.

        Returns:
            Applicative[B]: An Applicative containing the result of applying the function.
        """
        raise NotImplementedError()

    def __pow__[B](
        self,
        wrapped_funcs: Applicative[App, Callable[[A], B]],
    ) -> Applicative[App, B]:
        """
        Apply wrapped functions to this Applicative's value.

        Args:
            wrapped_funcs: An Applicative containing functions from A to B.

        Returns:
            Applicative[App, B]: An Applicative containing the result of applying the function.

        """
        return self.ap(wrapped_funcs)
