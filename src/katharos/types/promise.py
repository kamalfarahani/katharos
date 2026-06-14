from __future__ import annotations

import threading
from typing import Any, Callable, cast

from katharos.algebra import Applicative, Monad
from katharos.types.maybe import Maybe


class Promise[A](Monad["Promise[Any]", A]):
    """A lazy, synchronous computation monad.

    ``Promise`` wraps a zero-argument callable (the *fetch* function) whose
    return value is produced on demand.  The computation is not run until
    :meth:`resolve` is called, which caches the result so the fetch function
    runs at most once.

    It implements the :class:`~katharos.algebra.Monad`,
    :class:`~katharos.algebra.Applicative`, and
    :class:`~katharos.algebra.Functor` interfaces, so computations can be
    composed without triggering execution.

    Examples:
        >>> p = Promise(fetcher=lambda: 21)
        >>> p.fmap(lambda x: x * 2).resolve()
        42

        >>> add_one = Promise(fetcher=lambda: lambda x: x + 1)
        >>> Promise(fetcher=lambda: 10) ** add_one
        Promise(...)
        >>> (Promise(fetcher=lambda: 10) ** add_one).resolve()
        11

        >>> Promise(fetcher=lambda: 3) | (lambda x: Promise(fetcher=lambda: x * 10))
        Promise(...)
        >>> (Promise(fetcher=lambda: 3) | (lambda x: Promise(fetcher=lambda: x * 10))).resolve()
        30

    Note:
        Supports the ``|`` (bind) and ``**`` (applicative apply) operators.
        The first call to :meth:`resolve` evaluates the full computation chain
        and memoizes the result.
    """

    @classmethod
    def pure[T](cls, x: T) -> Promise[T]:
        """Wrap a value in an already-resolved Promise.

        Args:
            x: The value to wrap.

        Returns:
            A Promise that immediately yields ``x`` when resolved.

        Examples:
            >>> Promise.pure(42).resolve()
            42
        """
        return Promise[T](fetcher=lambda: x)

    @classmethod
    def ret[T](cls, x: T) -> Promise[T]:
        """Wrap a value in an already-resolved Promise.

        Alias for :meth:`pure`, provided to satisfy the Monad interface.

        Args:
            x: The value to wrap.

        Returns:
            A Promise that immediately yields ``x`` when resolved.

        Examples:
            >>> Promise.ret("hello").resolve()
            'hello'
        """
        return cls.pure(x)

    def __init__(
        self,
        fetcher: Callable[[], A],
    ) -> None:
        """Initialize a Promise with a fetcher callable.

        Args:
            fetcher: A zero-argument callable whose return value is the
                result of this Promise.  It is called lazily the first
                time :meth:`resolve` is invoked.
        """
        self._value = Maybe[A].Nothing()
        self._error = Maybe[BaseException].Nothing()
        self._fetcher = fetcher
        self._lock = threading.Lock()

    def ap[B](
        self,
        wrapped_funcs: Applicative[Promise, Callable[[A], B]],
    ) -> Promise[B]:
        """Apply a function wrapped in a Promise to this Promise's value.

        Both this Promise and ``wrapped_funcs`` are evaluated lazily; neither
        is run until the returned Promise is resolved.

        Args:
            wrapped_funcs: A Promise containing a function ``A -> B`` to apply.

        Returns:
            A new Promise that, when resolved, applies the fetched function
            to the fetched value.

        Examples:
            >>> double = Promise(fetcher=lambda: lambda x: x * 2)
            >>> (Promise(fetcher=lambda: 5) ** double).resolve()
            10
        """
        wrapped_funcs = cast(Promise[Callable[[A], B]], wrapped_funcs)

        return Promise(lambda: wrapped_funcs.resolve()(self.resolve()))

    def bind[B](self, f: Callable[[A], Monad[Promise, B]]) -> Promise[B]:
        """Chain a function that returns a Promise.

        Args:
            f: A function that takes the resolved value and returns a new
                ``Promise[B]``.

        Returns:
            A new Promise that, when resolved, resolves this Promise and then
            resolves the Promise returned by ``f``.

        Examples:
            >>> (Promise(fetcher=lambda: 3) | (lambda x: Promise.pure(x + 7))).resolve()
            10
        """
        f = cast(Callable[[A], Promise[B]], f)
        promise_b = Promise(lambda: f(self.resolve()).resolve())

        return promise_b

    def fmap[B](self, f: Callable[[A], B]) -> Promise[B]:
        """Map a pure function over the wrapped value.

        Args:
            f: A function to apply to the resolved value.

        Returns:
            A new Promise that applies ``f`` to the result of this Promise
            when resolved.

        Examples:
            >>> Promise(fetcher=lambda: 4).fmap(lambda x: x ** 2).resolve()
            16
        """
        return Promise(lambda: f(self.resolve()))

    def resolve(self) -> A:
        """Execute the fetcher and memoize its result.

        The fetcher is run at most once: the resolved value is cached so
        subsequent calls return it without re-executing. If the fetcher
        raises, the exception is cached too and re-raised on every
        subsequent call, so failure is also evaluated at most once.

        Evaluation is guarded by a per-Promise lock, so concurrent calls
        from multiple threads still run the fetcher exactly once; the
        losing threads block until the result (or error) is cached.

        Returns:
            The resolved value.

        Raises:
            BaseException: Whatever the fetcher raised. Cached on the first
                failure and re-raised on each subsequent call.

        Examples:
            >>> Promise(fetcher=lambda: 6).resolve()
            6
        """
        with self._lock:
            if self._value.is_just():
                return self._value.unwrap()

            if self._error.is_just():
                raise self._error.unwrap()

            try:
                value = self._fetcher()
            except BaseException as e:
                self._error = Maybe[BaseException].Just(e)
                raise
            else:
                self._value = Maybe[A].Just(value)
                return value

    def __pow__[B](
        self,
        wrapped_funcs: Applicative[Promise, Callable[[A], B]],
    ) -> Promise[B]:
        """Infix operator for applicative application (``**``).

        Args:
            wrapped_funcs: A Promise containing a function to apply.

        Returns:
            A new Promise containing the result of applying the function.
        """
        return self.ap(wrapped_funcs)

    def __or__[B](self, f: Callable[[A], Monad[Promise, B]]) -> Promise[B]:
        """Infix operator for monadic bind (``|``).

        Args:
            f: A function that takes the resolved value and returns a
                ``Promise[B]``.

        Returns:
            The Promise returned by ``f`` after resolving this Promise.
        """
        return self.bind(f)

    def __rshift__[B](self, other: Monad[Promise, B]) -> Promise[B]:
        """Infix operator for sequencing (``>>``).

        Discards the result of this Promise and returns ``other``.

        Args:
            other: The Promise to return after this one resolves.

        Returns:
            ``other``, ignoring the value of this Promise.
        """
        return super().__rshift__(other)  # type: ignore

    def __repr__(self) -> str:
        """Return the string representation of this Promise.

        Returns:
            A string of the form ``Promise(<fetcher>)``.
        """
        return f"Promise({self._fetcher})"
