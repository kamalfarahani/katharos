from __future__ import annotations

from abc import ABC
from collections.abc import Callable

from katharos.algebra.monad import Monad


class Maybe[A](Monad[A], ABC):
    """
    This class represents a Maybe type.
    """

    @classmethod
    def pure(cls: type[Maybe], x: A) -> Maybe[A]:
        """
        Return a Maybe containing the given value.

        Args:
            x: The value to wrap in a Maybe.

        Returns:
            Maybe[A]: A Just containing the given value.
        """
        return Just(value=x)


class Nothing[A](Maybe[A]):
    """
    This class represents a Nothing value
    """

    def fmap[B](self, f: Callable[[A], B]) -> Nothing[B]:
        """
        fmap over a Nothing returns a Nothing.

        Args:
            f: The function to apply.

        Returns:
            Maybe[B]: A Nothing.
        """
        return Nothing()

    def ap[B](self, wrapped_funcs: Maybe[Callable[[A], B]]) -> Nothing[B]:
        """
        apply a Nothing returns a Nothing.

        Args:
            wrapped_funcs: The function to apply.

        Returns:
            Maybe[B]: A Nothing.
        """
        return Nothing()

    def bind[B](self, f: Callable[[A], Maybe[B]]) -> Nothing[B]:
        """
        bind a Nothing returns a Nothing.

        Args:
            f: The function to apply.

        Returns:
            Maybe[B]: A Nothing.
        """
        return Nothing()


class Just[A](Maybe[A]):
    """
    This class represents a Just value
    """

    __match_args__ = ("value",)

    def __init__(self, value: A) -> None:
        """
        Initialize the Just with a value.

        Args:
            value: The value to wrap in a Just.
        """
        self._value = value

    @property
    def value(self) -> A:
        """
        Returns the value of Just.

        Returns:
            A: The value of Just.
        """
        return self._value

    def fmap[B](self, f: Callable[[A], B]) -> Just[B]:
        """
        fmap a function over a Just value.

        Args:
            f: The function to apply to the value.

        Returns:
            Just[B]: A Just containing the result of applying f to the value.
        """
        return Just(f(self.value))

    def ap[B](self, wrapped_funcs: Maybe[Callable[[A], B]]) -> Maybe[B]:
        """
        Apply wrapped functions to this Just's value.

        Args:
            wrapped_funcs: A Maybe containing a function from A to B.

        Returns:
            Maybe[B]: A Just containing the result of applying the function,
                      or Nothing if wrapped_funcs is Nothing.
        """
        match wrapped_funcs:
            case Just(value=func):
                return Just(func(self.value))
            case _:
                return Nothing()

    def bind[B](
        self,
        f: Callable[[A], Maybe[B]],
    ) -> Maybe[B]:
        """
        Bind a function to the Just value.

        Args:
            f: A function that takes a value of type A and returns a Maybe of type B.

        Returns:
            Maybe[B]: The result of applying f to the contained value.
        """
        return f(self.value)
