from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, Self, TypeVar

from katharos.algebra.functor.functor import Functor

App = TypeVar("App", bound="Applicative[Any, Any]", covariant=True)
A = TypeVar("A", covariant=True)


class Applicative(Functor[App, A], ABC):
    """Abstract base class for applicative functors.

    An applicative functor extends :class:`~katharos.algebra.Functor` with the
    ability to apply functions wrapped in a context to values wrapped in a
    context. It sits between :class:`~katharos.algebra.Functor` and
    :class:`~katharos.algebra.Monad` in the abstraction hierarchy.

    Use :meth:`pure` to lift a plain value into the applicative context, and
    the ``**`` operator (or :meth:`ap`) to apply a wrapped function to a
    wrapped value.

    Note:
        Instances must satisfy the applicative laws (where ``App`` is the
        concrete applicative type and ``id`` / ``compose`` are the identity and
        composition functions):

        - **Identity**: ``v ** App.pure(id) == v``
        - **Composition**: ``w ** (v ** (u ** App.pure(compose))) == (w ** v) ** u``
        - **Homomorphism**: ``App.pure(x) ** App.pure(f) == App.pure(f(x))``
        - **Interchange**: ``App.pure(y) ** u == u ** App.pure(lambda f: f(y))``
    """

    @classmethod
    @abstractmethod
    def pure[T](cls: type[Self], x: T) -> Applicative[App, T]:
        """Lift a value into the applicative context.

        Args:
            x: The value to wrap in an applicative.

        Returns:
            An applicative containing the given value.
        """
        raise NotImplementedError()

    @abstractmethod
    def ap[B](
        self,
        wrapped_funcs: Applicative[App, Callable[[A], B]],
    ) -> Applicative[App, B]:
        """Apply wrapped functions to this applicative's value.

        Args:
            wrapped_funcs: An applicative containing functions from A to B.

        Returns:
            An applicative containing the result of applying the function.
        """
        raise NotImplementedError()

    def __pow__[B](
        self,
        wrapped_funcs: Applicative[App, Callable[[A], B]],
    ) -> Applicative[App, B]:
        """Infix operator for applicative application (``**``).

        Args:
            wrapped_funcs: An applicative containing functions from A to B.

        Returns:
            An applicative containing the result of applying the function.
        """
        return self.ap(wrapped_funcs)
