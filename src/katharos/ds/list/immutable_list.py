from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any, TypeVar, cast

from katharos.algebra import Monad, Monoid
from katharos.algebra.applicative.applicative import Applicative

from .base_immutable_list import BaseImmutableList

T = TypeVar(name="T", covariant=True)


class ImmutableList(
    BaseImmutableList[T],
    Monad["ImmutableList[Any]", T],
    Monoid["ImmutableList[T]"],
):
    """
    A covariant immutable list implementation.

    This class provides an immutable wrapper around a list, ensuring that the
    underlying data cannot be modified after creation. The type parameter T is
    covariant, meaning that ImmutableList[Child] is a subtype of ImmutableList[Parent]
    when Child is a subtype of Parent.

    The immutable nature makes instances hashable and safe to use as dictionary keys
    or in sets. All standard sequence operations are supported for read-only access.

    Args:
        elements: The list of elements to wrap. A copy is not made, so the original
                 list should not be modified after passing it to this constructor.

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

        # Covariance example:
        >>> strings: ImmutableList[str] = ImmutableList(["hello", "world"])
        >>> objects: ImmutableList[object] = strings  # Valid due to covariance
    """

    def __eq__(self, other: object) -> bool:
        """
        Return True if the list is equal to the other object, False otherwise.

        Args:
            other: The object to compare to.

        Returns:
            bool: True if the list is equal to the other object, False otherwise.
        """
        if not isinstance(other, ImmutableList):
            return False
        return self._elements == other._elements

    def __hash__(self) -> int:
        """
        Return the hash value of the list.

        Returns:
            int: The hash value of the list.
        """
        return hash(tuple(self._elements))

    def __repr__(self) -> str:
        """
        Return a string representation of the list.

        Returns:
            str: A string representation of the list.
        """
        return f"ImmutableList({self._elements!r})"

    def __str__(self) -> str:
        """
        Return a string representation of the list.

        Returns:
            str: A string representation of the list.
        """
        return str(self._elements)

    def __add__(self, other: Iterable[T]) -> ImmutableList[T]:
        """
        Return a new ImmutableList containing the elements of the list and the other list.

        Args:
            other: The list to add to the list.

        Returns:
            ImmutableList[T]: A new ImmutableList containing the elements of the list and the other list.
        """
        return ImmutableList(list(self) + list(other))

    @classmethod
    def identity(cls: type[ImmutableList[T]]) -> ImmutableList[T]:
        """
        Return the identity element for the monoid operation.

        Returns:
            ImmutableList[T]: An empty ImmutableList.
        """
        return ImmutableList([])

    @classmethod
    def pure[T_1](cls: type[ImmutableList[T_1]], x: T_1) -> ImmutableList[T_1]:
        """
        Return a singleton ImmutableList containing the given element.

        Args:
            x: The element to wrap in an ImmutableList.

        Returns:
            ImmutableList[T]: An ImmutableList containing only the given element.
        """
        return ImmutableList([x])

    def op(self, other: ImmutableList[T]) -> ImmutableList[T]:
        """
        Combine this ImmutableList with another using concatenation (monoid operation).

        Args:
            other: Another ImmutableList to concatenate with this one.

        Returns:
            ImmutableList[T]: A new ImmutableList containing elements from both lists.
        """
        return self + other

    def fmap[B](self, f: Callable[[T], B]) -> ImmutableList[B]:
        """
        Map a function over the elements of this ImmutableList.

        Args:
            f: A function to apply to each element.

        Returns:
            ImmutableList[B]: A new ImmutableList with the function applied to each element.
        """
        return ImmutableList(map(f, self._elements))

    def ap[B](
        self,
        wrapped_funcs: Applicative[ImmutableList, Callable[[T], B]],
    ) -> ImmutableList[B]:
        """
        Apply functions in this ImmutableList to values in another ImmutableList.

        Args:
            wrapped_funcs: An ImmutableList of functions to apply.

        Returns:
            ImmutableList[B]: A new ImmutableList with results of applying functions.
        """
        wrapped_funcs = cast(ImmutableList[Callable[[T], B]], wrapped_funcs)
        return ImmutableList[B]([f(x) for f in wrapped_funcs for x in self])

    def bind[B](
        self,
        f: Callable[[T], Monad[ImmutableList, B]],
    ) -> ImmutableList[B]:
        """
        Bind (flatMap) this ImmutableList with a function that returns another Monad.

        Args:
            f: A function that takes an element and returns an ImmutableList.

        Returns:
            ImmutableList[B]: A new ImmutableList with the results of applying the function.
        """
        f = cast(Callable[[T], ImmutableList[B]], f)
        return ImmutableList[B]([x for elem in self for x in f(elem)])

    def __matmul__(self, other: ImmutableList[T]) -> ImmutableList[T]:
        """
        Infix operator for semigroup operation (concatenation).
        Enables syntax like list1 @ list2 for concatenation.
        Equivalent to the + operator.

        Args:
            other: Another ImmutableList to concatenate with this one.

        Returns:
            ImmutableList[T]: A new ImmutableList containing all elements from both lists.
        """
        return self.op(other)

    def __pow__[B](
        self,
        wrapped_funcs: Applicative[ImmutableList, Callable[[T], B]],
    ) -> ImmutableList[B]:
        """
        Apply functions using the applicative style (** operator).
        This enables applicative-style function application.

        Args:
            wrapped_funcs: An Applicative of functions to apply.

        Returns:
            ImmutableList[B]: A new ImmutableList with results of applying functions.
        """
        return self.ap(wrapped_funcs)

    def __or__[B](
        self,
        f: Callable[[T], Monad[ImmutableList, B]],
    ) -> ImmutableList[B]:
        """
        Chain operations using the Kleisli composition (|) operator.
        This enables monadic chaining where each function returns a Monad.

        Args:
            f: A function that takes an element and returns a Monad[ImmutableList, B].

        Returns:
            ImmutableList[B]: A new ImmutableList with the results of chaining operations.
        """
        return self.bind(f)
