from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable

from katharos.algebra.applicative.applicative import Applicative


class Monad[Mon, A](Applicative[Mon, A], ABC):
    """Abstract base class for monads.

    A monad extends :class:`~katharos.algebra.Applicative` with the ``bind``
    operation (``>>=`` in Haskell, exposed as ``|``), which allows sequencing
    computations that produce monadic values.

    Use :meth:`ret` to lift a plain value, and ``|`` (or :meth:`bind`) to
    chain computations. Use ``>>`` (or :meth:`then`) to sequence actions while
    discarding the first result.

    Note:
        Instances must satisfy the monad laws:

        - **Left identity**: ``ret(a).bind(f) == f(a)``
        - **Right identity**: ``m.bind(ret) == m``
        - **Associativity**: ``m.bind(f).bind(g) == m.bind(lambda x: f(x).bind(g))``

    Examples:
        Using ``bind`` (``|`` operator)::

            m = SomeMonad.ret(5)
            result = m | (lambda x: SomeMonad.ret(x * 2))

        Sequencing with ``then`` (``>>`` operator)::

            m1 = SomeMonad.ret(1)
            m2 = SomeMonad.ret(2)
            result = m1 >> m2  # returns m2, discarding m1's value
    """

    @classmethod
    def ret[T](cls: type[Monad[Mon, T]], x: T) -> Monad[Mon, T]:
        """Wrap a value in the monad.

        Args:
            x: The value to wrap.

        Returns:
            A monad containing the given value.
        """
        return cls.pure(x)  # type: ignore[return-value]

    @abstractmethod
    def bind[B](
        self,
        f: Callable[[A], Monad[Mon, B]],
    ) -> Monad[Mon, B]:
        """Chain this monad with a function that returns a monad.

        Args:
            f: A function that takes a value of type A and returns a monad
                of type B.

        Returns:
            A monad containing the result of applying the function.
        """
        raise NotImplementedError()

    def then[B](self, other: Monad[Mon, B]) -> Monad[Mon, B]:
        """Sequence two monadic actions, discarding the first result.

        Args:
            other: The monad to sequence after this one.

        Returns:
            The result of the second monad.
        """
        return self | (lambda _: other)

    def __or__[B](self, f: Callable[[A], Monad[Mon, B]]) -> Monad[Mon, B]:
        """Infix operator for monadic bind (``|``).

        Args:
            f: A function that takes a value of type A and returns a monad
                of type B.

        Returns:
            A monad containing the result of applying the function.
        """
        return self.bind(f)

    def __rshift__[B](self, other: Monad[Mon, B]) -> Monad[Mon, B]:
        """Infix operator for sequencing two monadic actions (``>>``).

        Args:
            other: The monad to sequence after this one.

        Returns:
            The result of the second monad.
        """
        return self.then(other)
