from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Self

from katharos.algebra.applicative.applicative import Applicative


class Monad[A](Applicative[A], ABC):
    """
    A Monad is a monadic type that represents a computation that can be sequenced.

    A Monad extends Applicative and provides the `bind` operation (also known as
    flatMap or >>=) which allows sequencing computations that produce monadic values.

    Monad Laws:
    -----------
    All instances of Monad must satisfy the following three laws:

    1. Left Identity:
       ret(a).bind(f) == f(a)

       Wrapping a value in a monad and binding it with a function should be
       the same as applying the function directly to the value.

    2. Right Identity:
       m.bind(ret) == m

       Binding a monad with the `ret` function should return the original monad.

    3. Associativity:
       m.bind(f).bind(g) == m.bind(lambda x: f(x).bind(g))

       The order of binding operations should not matter. Chaining binds should
       be associative.

    Type Parameters:
    ----------------
    A : The type of value contained in the Monad.

    Abstract Methods:
    -----------------
    bind : Sequence a monadic computation with a function that returns a Monad.

    Examples:
    ---------
    Using the bind operation:
        >>> m = SomeMonad.ret(5)
        >>> result = m.bind(lambda x: SomeMonad.ret(x * 2))

    Using the | operator (infix bind):
        >>> m = SomeMonad.ret(5)
        >>> result = m | (lambda x: SomeMonad.ret(x * 2))

    Sequencing monads with skip (>>):
        >>> m1 = SomeMonad.ret(1)
        >>> m2 = SomeMonad.ret(2)
        >>> result = m1 >> m2  # Returns m2, discarding m1's value
    """

    @staticmethod
    def ret(x: A) -> Self:
        """
        Return a Monad containing the given value.

        Args:
            x: The value to wrap in a Monad.

        Returns:
            Self: A Monad containing the given value.
        """
        return Monad.pure(x)

    @abstractmethod
    def bind[B](
        self,
        f: Callable[[A], Monad[B]],
    ) -> Monad[B]:
        """
        Monad bind operation.

        Args:
            f: A function that takes a value of type A and returns a Monad of type B.

        Returns:
            Monad[B]: A Monad containing the result of applying the function to the value.
        """
        raise NotImplementedError()

    def skip[B](self, other: Monad[B]) -> Monad[B]:
        """
        Sequence two monadic actions, discarding the result of the first.

        This is equivalent to `self.bind(lambda _: other)`.

        Args:
            other: The Monad to sequence after this one.

        Returns:
            Monad[B]: The result of the second Monad.
        """
        return other

    def __or__[B](self, f: Callable[[A], Monad[B]]) -> Monad[B]:
        """
        Infix operator for bind.

        Args:
            f: A function that takes a value of type A and returns a Monad of type B.

        Returns:
            Monad[B]: A Monad containing the result of applying the function to the value.
        """
        return self.bind(f)

    def __rshift__[B](self, other: Monad[B]) -> Monad[B]:
        """
        Infix operator for skip (sequence two monadic actions).

        Args:
            other: The Monad to sequence after this one.

        Returns:
            Monad[B]: The result of the second Monad.
        """
        return self.skip(other)
