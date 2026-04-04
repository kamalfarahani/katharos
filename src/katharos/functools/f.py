import inspect
from collections.abc import Callable, Iterable
from functools import wraps
from operator import matmul

from katharos.algebra import Semigroup
from katharos.ds.list import NonEmptyList


class F:
    """
    This class serves as a namespace for utility functions.
    All functions are static and can be called without instantiating the class.
    """

    @staticmethod
    def compose[A, B, C](
        f: Callable[[B], C],
    ) -> Callable[[Callable[[A], B]], Callable[[A], C]]:
        """
        Compose two functions.

        Args:
            f: A function from B to C

        Returns:
            A function that takes a function from A to B and returns a function from A to C
        """

        def inner(g: Callable[[A], B]) -> Callable[[A], C]:
            return lambda x: f(g(x))

        return inner

    @staticmethod
    def id[A](x: A) -> A:
        """
        Identity function.

        Args:
            x: Input value

        Returns:
            The same value x
        """
        return x

    @staticmethod
    def foldr[A, B](
        f: Callable[[A, B], B],
        acc: B,
        xs: Iterable[A],
    ) -> B:
        """
        Right fold a function over an iterable.

        Args:
            f: A function that takes an element and an accumulator and returns a new accumulator
            acc: The initial accumulator value
            xs: An iterable of elements

        Returns:
            The accumulator value after applying f to each element of xs
        """
        result = acc
        for x in reversed(list(xs)):
            result = f(x, result)

        return result

    @staticmethod
    def foldl[A, B](
        f: Callable[[B, A], B],
        acc: B,
        xs: Iterable[A],
    ) -> B:
        """
        Left fold a function over an iterable.

        Args:
            f: A function that takes an accumulator and an element and returns a new accumulator
            acc: The initial accumulator value
            xs: An iterable of elements

        Returns:
            The accumulator value after applying f to each element of xs
        """
        result = acc
        for x in xs:
            result = f(result, x)

        return result

    @staticmethod
    def sigma[A: Semigroup](xs: NonEmptyList[A]) -> A:
        """
        Combine all elements of a non-empty list using the semigroup operation.

        Args:
            xs: A non-empty list of semigroup elements

        Returns:
            A: The result of combining all elements using the semigroup's @ operator
        """
        return F.foldl(
            matmul,
            xs.head,
            xs.tail,
        )

    @staticmethod
    def curry(f: Callable) -> Callable:
        """
        Transform a multi-argument function into a curried version.

        Currying converts a function that takes multiple arguments into a sequence
        of functions, each taking a single argument.

        Args:
            f: A function to curry

        Returns:
            A curried version of the function

        Examples:
            >>> def add(x: int, y: int, z: int) -> int:
            ...     return x + y + z
            >>> curried_add = F.curry(add)
            >>> curried_add(1)(2)(3)
            6
            >>> add_one = curried_add(1)
            >>> add_one(2)(3)
            6
        """
        sig = inspect.signature(f)
        params = list(sig.parameters.values())
        num_params = len(params)

        if num_params == 0:
            return f

        @wraps(f)
        def curried(*args):
            if len(args) >= num_params:
                return f(*args[:num_params])

            def partial(*more_args):
                return curried(*(args + more_args))

            return partial

        return curried
