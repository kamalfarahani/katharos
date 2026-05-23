from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any, TypeVar, cast  # noqa: F401

from katharos.algebra import Monad, Monoid
from katharos.algebra.applicative.applicative import Applicative

from .base_immutable_list import BaseImmutableList

T = TypeVar(name="T", covariant=True)


class ImmutableList(
    BaseImmutableList[T],
    Monad["ImmutableList[Any]", T],
    Monoid["ImmutableList[T]"],
):
    """A covariant immutable list with full monad and monoid support.

    Provides an immutable wrapper around a Python list. The type parameter
    ``T`` is covariant, so ``ImmutableList[Child]`` is a subtype of
    ``ImmutableList[Parent]`` when ``Child`` is a subtype of ``Parent``.

    Instances are hashable and safe to use as dictionary keys or set members.
    All standard sequence operations are supported for read-only access.

    Examples:
        >>> numbers = ImmutableList([1, 2, 3, 4, 5])
        >>> len(numbers)
        5
        >>> 3 in numbers
        True
        >>> numbers[1]
        2
        >>> list(numbers)
        [1, 2, 3, 4, 5]
        >>> numbers + [6, 7]
        ImmutableList([1, 2, 3, 4, 5, 6, 7])
    """

    def __eq__(self, other: object) -> bool:
        """Check equality with another ImmutableList.

        Args:
            other: The object to compare with.

        Returns:
            True if ``other`` is an ImmutableList with identical elements.
        """
        if not isinstance(other, ImmutableList):
            return False
        return self._elements == other._elements

    def __hash__(self) -> int:
        """Return a hash of the list contents.

        Returns:
            Hash of the element tuple.
        """
        return hash(tuple(self._elements))

    def __repr__(self) -> str:
        """Return the canonical string representation of this list.

        Returns:
            ``ImmutableList([...])`` with the element list.
        """
        return f"ImmutableList({self._elements!r})"

    def __str__(self) -> str:
        """Return the string form of the underlying element list.

        Returns:
            The string representation of the internal Python list.
        """
        return str(self._elements)

    def __add__(self, other: Iterable[T]) -> ImmutableList[T]:
        """Concatenate this list with another iterable.

        Args:
            other: The elements to append.

        Returns:
            A new ImmutableList containing elements from both sequences.
        """
        return ImmutableList(list(self) + list(other))

    @classmethod
    def identity(cls: type[ImmutableList[T]]) -> ImmutableList[T]:
        """Return the identity element for the monoid operation.

        Returns:
            An empty ImmutableList.
        """
        return ImmutableList([])

    @classmethod
    def pure[T_1](cls: type[ImmutableList[T_1]], x: T_1) -> ImmutableList[T_1]:
        """Wrap a single value in an ImmutableList.

        Args:
            x: The element to wrap.

        Returns:
            A singleton ImmutableList containing only ``x``.
        """
        return ImmutableList([x])

    @classmethod
    def ret[T_1](cls: type[ImmutableList[T_1]], x: T_1) -> ImmutableList[T_1]:
        """Wrap a single value in an ImmutableList.

        Alias for :meth:`pure`, provided to satisfy the Monad interface.

        Args:
            x: The element to wrap.

        Returns:
            A singleton ImmutableList containing only ``x``.
        """
        return cls.pure(x)

    def op(self, other: ImmutableList[T]) -> ImmutableList[T]:
        """Combine this list with another using concatenation.

        Args:
            other: Another ImmutableList to concatenate with.

        Returns:
            A new ImmutableList containing elements from both lists.
        """
        return self + other

    def fmap[B](self, f: Callable[[T], B]) -> ImmutableList[B]:
        """Map a function over every element.

        Args:
            f: A function to apply to each element.

        Returns:
            A new ImmutableList with the function applied to each element.
        """
        return ImmutableList(map(f, self._elements))

    def ap[B](
        self,
        wrapped_funcs: Applicative[ImmutableList, Callable[[T], B]],
    ) -> ImmutableList[B]:
        """Apply each wrapped function to each element (cartesian product).

        Args:
            wrapped_funcs: An ImmutableList of functions to apply.

        Returns:
            A new ImmutableList with results of applying every function to
            every element.
        """
        wrapped_funcs = cast(ImmutableList[Callable[[T], B]], wrapped_funcs)
        return ImmutableList[B]([f(x) for f in wrapped_funcs for x in self])

    def bind[B](
        self,
        f: Callable[[T], Monad[ImmutableList, B]],
    ) -> ImmutableList[B]:
        """Flatmap this list with a function that returns a list (concatMap).

        Args:
            f: A function that takes an element and returns an ImmutableList.

        Returns:
            A new ImmutableList with the results of all returned lists
            concatenated.
        """
        f = cast(Callable[[T], ImmutableList[B]], f)
        return ImmutableList[B]([x for elem in self for x in f(elem)])

    def __matmul__(self, other: ImmutableList[T]) -> ImmutableList[T]:
        """Infix operator for the semigroup concatenation (``@``).

        Args:
            other: Another ImmutableList to concatenate with.

        Returns:
            A new ImmutableList containing all elements from both lists.
        """
        return self.op(other)

    def __pow__[B](
        self,
        wrapped_funcs: Applicative[ImmutableList, Callable[[T], B]],
    ) -> ImmutableList[B]:
        """Infix operator for applicative application (``**``).

        Args:
            wrapped_funcs: An ImmutableList of functions to apply.

        Returns:
            A new ImmutableList with results of applying every function to
            every element.
        """
        return self.ap(wrapped_funcs)

    def __or__[B](
        self,
        f: Callable[[T], Monad[ImmutableList, B]],
    ) -> ImmutableList[B]:
        """Infix operator for monadic bind (``|``).

        Args:
            f: A function that takes an element and returns an ImmutableList.

        Returns:
            A new ImmutableList with all returned lists concatenated.
        """
        return self.bind(f)
