import inspect
from collections.abc import Callable, Iterable
from functools import wraps
from operator import matmul
from typing import Any, overload

from katharos.algebra import Applicative, Semigroup
from katharos.types.list import NonEmptyList


class F:
    """Namespace for utility functions.

    All functions are static and can be called without instantiating the class.
    """

    @staticmethod
    def compose[A, B, C](
        f: Callable[[B], C],
    ) -> Callable[[Callable[[A], B]], Callable[[A], C]]:
        """Compose two functions.

        Args:
            f: A function from B to C.

        Returns:
            A function that takes a function from A to B and returns a function
            from A to C.

        Examples:
            >>> inc = lambda x: x + 1
            >>> double = lambda x: x * 2
            >>> inc_then_double = F.compose(double)(inc)
            >>> inc_then_double(5)
            12
        """

        def inner(g: Callable[[A], B]) -> Callable[[A], C]:
            return lambda x: f(g(x))

        return inner

    @staticmethod
    def id[A](x: A) -> A:
        """Identity function.

        Args:
            x: Input value.

        Returns:
            The same value x.

        Examples:
            >>> F.id(42)
            42
            >>> F.id("hello")
            'hello'
        """
        return x

    @staticmethod
    def foldr[A, B](
        f: Callable[[A, B], B],
        acc: B,
        xs: Iterable[A],
    ) -> B:
        """Right fold a function over an iterable.

        Args:
            f: A function that takes an element and an accumulator and returns a
                new accumulator.
            acc: The initial accumulator value.
            xs: An iterable of elements.

        Returns:
            The accumulator value after applying f to each element of xs.

        Examples:
            >>> F.foldr(lambda x, acc: acc + [x], [], [1, 2, 3])
            [3, 2, 1]
            >>> F.foldr(lambda x, acc: f"({x}+{acc})", "0", [1, 2, 3])
            '(1+(2+(3+0)))'
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
        """Left fold a function over an iterable.

        Args:
            f: A function that takes an accumulator and an element and returns a
                new accumulator.
            acc: The initial accumulator value.
            xs: An iterable of elements.

        Returns:
            The accumulator value after applying f to each element of xs.

        Examples:
            >>> F.foldl(lambda acc, x: acc + x, 0, [1, 2, 3])
            6
            >>> F.foldl(lambda acc, x: f"({acc}+{x})", "0", [1, 2, 3])
            '(((0+1)+2)+3)'
        """
        result = acc
        for x in xs:
            result = f(result, x)

        return result

    @staticmethod
    def sigma[A: Semigroup](xs: NonEmptyList[A]) -> A:
        """Combine all elements of a non-empty list using the semigroup operation.

        Args:
            xs: A non-empty list of semigroup elements.

        Returns:
            The result of combining all elements using the semigroup's @ operator.

        Examples:
            >>> from katharos.types.list import NonEmptyList
            >>> from katharos.types.monoid import Sum
            >>> F.sigma(NonEmptyList(Sum(1), [Sum(2), Sum(3)]))
            Sum(6)
        """
        return F.foldl(
            matmul,
            xs.head,
            xs.tail,
        )

    @overload
    @staticmethod
    def curry[A, R](f: Callable[[A], R]) -> Callable[[A], R]: ...

    @overload
    @staticmethod
    def curry[A, B, R](f: Callable[[A, B], R]) -> Callable[[A], Callable[[B], R]]: ...

    @overload
    @staticmethod
    def curry[A, B, C, R](
        f: Callable[[A, B, C], R],
    ) -> Callable[[A], Callable[[B], Callable[[C], R]]]: ...

    @overload
    @staticmethod
    def curry(f: Callable[..., Any]) -> Callable[..., Any]: ...

    @staticmethod
    def curry(f: Callable[..., Any]) -> Callable[..., Any]:
        """Transform a multi-argument function into a curried version.

        Currying converts a function that takes multiple arguments into a sequence
        of functions, each taking a single argument. Supports both positional and
        keyword arguments, and several arguments may be supplied in one step.

        The original function is invoked as soon as every parameter without a
        default is bound.  Consequently, parameters with defaults (as well as
        ``*args``/``**kwargs``) can only be overridden in the step that
        completes the call — not in a later step, because there is no later
        step.

        Args:
            f: A function to curry.

        Returns:
            A curried version of the function.

        Raises:
            TypeError: If an argument does not match the function's signature,
                or a keyword argument is supplied more than once.

        Examples:
            >>> def add(x: int, y: int, z: int) -> int:
            ...     return x + y + z
            >>> curried_add = F.curry(add)
            >>> curried_add(1)(2)(3)
            6
            >>> add_one = curried_add(1)
            >>> add_one(2)(3)
            6
            >>> curried_add(x=1)(y=2)(z=3)
            6
            >>> curried_add(1, y=2)(z=3)
            6

            Parameters with defaults need not be supplied; the call fires once
            all required parameters are bound:

            >>> def greet(name: str, greeting: str = "hi") -> str:
            ...     return f"{greeting} {name}"
            >>> F.curry(greet)("bob")
            'hi bob'
            >>> F.curry(greet)("bob", greeting="hello")
            'hello bob'

            Supplying the same keyword twice is an error, as in a plain call:

            >>> curried_add(x=1)(x=2, y=2, z=3)
            Traceback (most recent call last):
                ...
            TypeError: add() got multiple values for keyword argument 'x'
        """
        sig = inspect.signature(f)
        num_params = len(sig.parameters)

        if num_params == 0:
            return f

        @wraps(f)
        def curried(*args, **kwargs):
            bound_args = sig.bind_partial(*args, **kwargs)
            bound_args.apply_defaults()

            if len(bound_args.arguments) >= num_params:
                return f(*args, **kwargs)

            @wraps(f)
            def partial(*more_args, **more_kwargs):
                return curried(*args, *more_args, **kwargs, **more_kwargs)

            return partial

        return curried

    @staticmethod
    def lift_a2[A, B, C, App: Applicative](
        f: Callable[[A, B], C],
        fa: Applicative[App, A],
        fb: Applicative[App, B],
    ) -> Applicative[App, C]:
        """Lift a binary function into an applicative context.

        Applies a two-argument function to the values held inside two
        applicatives of the same type, combining their contexts.

        Args:
            f: A function taking two arguments of types A and B.
            fa: An applicative containing a value of type A.
            fb: An applicative containing a value of type B.

        Returns:
            An applicative containing the result of applying f to the two
            wrapped values.

        Examples:
            >>> from katharos.types.maybe import Maybe
            >>> F.lift_a2(lambda x, y: x + y, Maybe.Just(2), Maybe.Just(3))
            Just(5)
            >>> F.lift_a2(lambda x, y: x + y, Maybe.Just(2), Maybe.Nothing())
            Nothing()
        """
        curried = F.curry(f)
        return fb.ap(fa.ap(fa.pure(curried)))

    @staticmethod
    def lift_a3[A, B, C, D, App: Applicative](
        f: Callable[[A, B, C], D],
        fa: Applicative[App, A],
        fb: Applicative[App, B],
        fc: Applicative[App, C],
    ) -> Applicative[App, D]:
        """Lift a ternary function into an applicative context.

        Applies a three-argument function to the values held inside three
        applicatives of the same type, combining their contexts.

        Args:
            f: A function taking three arguments of types A, B and C.
            fa: An applicative containing a value of type A.
            fb: An applicative containing a value of type B.
            fc: An applicative containing a value of type C.

        Returns:
            An applicative containing the result of applying f to the three
            wrapped values.

        Examples:
            >>> from katharos.types.maybe import Maybe
            >>> F.lift_a3(
            ...     lambda x, y, z: x + y + z,
            ...     Maybe.Just(1),
            ...     Maybe.Just(2),
            ...     Maybe.Just(3),
            ... )
            Just(6)
            >>> F.lift_a3(
            ...     lambda x, y, z: x + y + z,
            ...     Maybe.Just(1),
            ...     Maybe.Nothing(),
            ...     Maybe.Just(3),
            ... )
            Nothing()
        """
        curried = F.curry(f)
        return fc.ap(fb.ap(fa.ap(fa.pure(curried))))
