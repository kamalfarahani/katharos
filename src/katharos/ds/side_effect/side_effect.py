from __future__ import annotations

from abc import abstractmethod
from collections.abc import Callable
from typing import Self

from katharos.algebra import Monad


class SideEffect[A](Monad[A]):
    """
    This abstract class represents a side effect.
    It is an interface that defines the `effect()` method, which is
    responsible for executing the side effect.
    """

    def __init__(self, value: A) -> None:
        self._value = value

    @property
    def value(self) -> A:
        """
        Returns value inside side effect

        Returns:
            A: Value inside side effect
        """
        return self._value

    @classmethod
    def pure(cls: type[Self], x: A) -> Self:
        """
        Returns a side effect containing the value

        Args:
            x: The value to wrap in a SideEffect.

        Returns:
            SideEffect[A]: A SideEffect containing the given value.
        """
        return cls(x)

    def fmap[B](self, f: Callable[[A], B]) -> Self:
        """
        Map a function over the value in this SideEffect.

        Args:
            f: Function to apply to the value

        Returns:
            A new SideEffect containing the result of applying f to the value
        """
        return type(self)(f(self.value))

    def ap[B](
        self,
        wrapped_funcs: SideEffect[Callable[[A], B]],
    ) -> Self:
        """
        Apply a SideEffect containing a function to this SideEffect.

        Args:
            wrapped_funcs: A SideEffect containing a function to apply

        Returns:
            A new SideEffect with the result of applying the function
        """
        return type(self)(wrapped_funcs.value(self.value))

    def bind[B](
        self,
        f: Callable[[A], SideEffect[B]],
    ) -> SideEffect[B]:
        """
        Bind a function that returns a SideEffect to this SideEffect.

        Args:
            f: Function that takes the value and returns a SideEffect

        Returns:
            The result of applying f to the value
        """
        return f(self.value)

    @abstractmethod
    def effect(self) -> None:
        """
        Apply the side effect.

        This method is responsible for executing the side effect.
        It should not return anything.
        """
        raise NotImplementedError()

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.value!r})"
