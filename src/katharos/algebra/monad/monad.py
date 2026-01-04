from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable

from katharos.algebra.applicative.applicative import Applicative


class Monad[Mon, A](Applicative[Mon, A], ABC):
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

    Sequencing monads with sequence (>>):
        >>> m1 = SomeMonad.ret(1)
        >>> m2 = SomeMonad.ret(2)
        >>> result = m1 >> m2  # Returns m2, discarding m1's value
    """

    @classmethod
    def ret[T](cls: type[Monad[Mon, T]], x: T) -> Monad[Mon, T]:
        """
        Return a Monad containing the given value.

        Args:
            x: The value to wrap in a Monad.

        Returns:
            Monad[Mon, T]: A Monad containing the given value.
        """
        return cls.pure(x)  # type: ignore[return-value]

    @abstractmethod
    def bind[B](
        self,
        f: Callable[[A], Monad[Mon, B]],
    ) -> Monad[Mon, B]:
        """
        Monad bind operation.

        Args:
            f: A function that takes a value of type A and returns a Monad of type B.

        Returns:
            Monad[Mon, B]: A Monad containing the result of applying the function to the value.
        """
        raise NotImplementedError()

    def sequence[B](self, other: Monad[Mon, B]) -> Monad[Mon, B]:
        """
        Sequence two monadic actions, discarding the result of the first.

        Args:
            other: The Monad to sequence after this one.

        Returns:
            Monad[Mon, B]: The result of the second Monad.
        """
        return other

    def __or__[B](self, f: Callable[[A], Monad[Mon, B]]) -> Monad[Mon, B]:
        """
        Infix operator for bind.

        Args:
            f: A function that takes a value of type A and returns a Monad of type B.

        Returns:
            Monad[Mon, B]: A Monad containing the result of applying the function to the value.
        """
        return self.bind(f)

    def __rshift__[B](self, other: Monad[Mon, B]) -> Monad[Mon, B]:
        """
        Infix operator for sequence (sequence two monadic actions).

        Args:
            other: The Monad to sequence after this one.

        Returns:
            Monad[Mon, B]: The result of the second Monad.
        """
        return self.sequence(other)
