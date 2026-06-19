from __future__ import annotations

from typing import Any, Callable, cast  # noqa: F401  # Any used in "Lazy[Any]" base

from katharos.algebra import Applicative, Monad
from katharos.concurrency.base_threading_backend import BaseThreadingBackend
from katharos.concurrency.threading_backend import default_backend
from katharos.types.maybe import Maybe


class Lazy[A](Monad["Lazy[Any]", A]):
    """A lazy, synchronous computation monad.

    ``Lazy`` wraps a zero-argument callable (the *fetch* function) whose
    return value is produced on demand.  The computation is not run until
    :meth:`resolve` is called, which caches the result so the fetch function
    runs at most once.

    It implements the :class:`~katharos.algebra.Monad`,
    :class:`~katharos.algebra.Applicative`, and
    :class:`~katharos.algebra.Functor` interfaces, so computations can be
    composed without triggering execution.

    Examples:
        >>> p = Lazy(fetcher=lambda: 21)
        >>> p.fmap(lambda x: x * 2).resolve()
        42

        >>> add_one = Lazy(fetcher=lambda: lambda x: x + 1)
        >>> Lazy(fetcher=lambda: 10) ** add_one
        Lazy(...)
        >>> (Lazy(fetcher=lambda: 10) ** add_one).resolve()
        11

        >>> Lazy(fetcher=lambda: 3) | (lambda x: Lazy(fetcher=lambda: x * 10))
        Lazy(...)
        >>> (Lazy(fetcher=lambda: 3) | (lambda x: Lazy(fetcher=lambda: x * 10))).resolve()
        30

    Note:
        Supports the ``|`` (bind) and ``**`` (applicative apply) operators.
        The first call to :meth:`resolve` evaluates the full computation chain
        and memoizes the result.
    """

    @classmethod
    def pure[T](cls: type[Lazy[T]], x: T) -> Lazy[T]:
        """Wrap a value in a Lazy.

        Args:
            x: The value to wrap.

        Returns:
            A Lazy that yields ``x`` when resolved.

        Examples:
            >>> Lazy.pure(42).resolve()
            42
        """
        return cls(fetcher=lambda: x)

    @classmethod
    def ret[T](cls: type[Lazy[T]], x: T) -> Lazy[T]:
        """Wrap a value in a Lazy.

        Alias for :meth:`pure`, provided to satisfy the Monad interface.

        Args:
            x: The value to wrap.

        Returns:
            A Lazy that yields ``x`` when resolved.

        Examples:
            >>> Lazy.ret("hello").resolve()
            'hello'
        """
        return cls.pure(x)

    def __init__(
        self,
        fetcher: Callable[[], A],
        backend: BaseThreadingBackend | None = None,
    ) -> None:
        """Initialize a Lazy with a fetcher callable.

        Args:
            fetcher: A zero-argument callable whose return value is the
                result of this Lazy.  It is called lazily the first
                time :meth:`resolve` is invoked.
        """
        self._value = Maybe[A].Nothing()
        self._error = Maybe[BaseException].Nothing()
        self._fetcher = fetcher
        self._backend = backend or default_backend()
        self._lock = self._backend.create_lock()

    def ap[B](
        self,
        wrapped_funcs: Applicative[Lazy, Callable[[A], B]],
    ) -> Lazy[B]:
        """Apply a function wrapped in a Lazy to this Lazy's value.

        Both this Lazy and ``wrapped_funcs`` are evaluated lazily; neither
        is run until the returned Lazy is resolved.

        Args:
            wrapped_funcs: A Lazy containing a function ``A -> B`` to apply.

        Returns:
            A new Lazy that, when resolved, applies the fetched function
            to the fetched value.

        Examples:
            >>> double = Lazy(fetcher=lambda: lambda x: x * 2)
            >>> (Lazy(fetcher=lambda: 5) ** double).resolve()
            10
        """
        wrapped_funcs = cast(Lazy[Callable[[A], B]], wrapped_funcs)

        return Lazy(
            lambda: wrapped_funcs.resolve()(self.resolve()),
            backend=self._backend,
        )

    def bind[B](self, f: Callable[[A], Monad[Lazy, B]]) -> Lazy[B]:
        """Chain a function that returns a Lazy.

        Args:
            f: A function that takes the resolved value and returns a new
                ``Lazy[B]``.

        Returns:
            A new Lazy that, when resolved, resolves this Lazy and then
            resolves the Lazy returned by ``f``.

        Examples:
            >>> (Lazy(fetcher=lambda: 3) | (lambda x: Lazy.pure(x + 7))).resolve()
            10
        """
        f = cast(Callable[[A], Lazy[B]], f)
        lazy_b = Lazy(lambda: f(self.resolve()).resolve(), backend=self._backend)

        return lazy_b

    def fmap[B](self, f: Callable[[A], B]) -> Lazy[B]:
        """Map a pure function over the wrapped value.

        Args:
            f: A function to apply to the resolved value.

        Returns:
            A new Lazy that applies ``f`` to the result of this Lazy
            when resolved.

        Examples:
            >>> Lazy(fetcher=lambda: 4).fmap(lambda x: x ** 2).resolve()
            16
        """
        return Lazy(lambda: f(self.resolve()), backend=self._backend)

    def resolve(self) -> A:
        """Execute the fetcher and memoize its result.

        The fetcher is run at most once: the resolved value is cached so
        subsequent calls return it without re-executing. If the fetcher
        raises, the exception is cached too and re-raised on every
        subsequent call, so failure is also evaluated at most once.

        Evaluation is guarded by a per-Lazy lock, so concurrent calls
        from multiple threads still run the fetcher exactly once; the
        losing threads block until the result (or error) is cached.

        .. warning::
            The guard lock is not reentrant. A fetcher that calls
            :meth:`resolve` on the *same* Lazy (directly or indirectly)
            will deadlock.

            For example, this never completes because the fetcher tries to
            acquire the same lock already held by the outer ``resolve`` call::

                lazy = Lazy(lambda: lazy.resolve())
                lazy.resolve()

        Returns:
            The resolved value.

        Raises:
            BaseException: Whatever the fetcher raised. Cached on the first
                failure and re-raised on each subsequent call.

        Examples:
            >>> Lazy(fetcher=lambda: 6).resolve()
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
        wrapped_funcs: Applicative[Lazy, Callable[[A], B]],
    ) -> Lazy[B]:
        """Infix operator for applicative application (``**``).

        Args:
            wrapped_funcs: A Lazy containing a function to apply.

        Returns:
            A new Lazy containing the result of applying the function.
        """
        return self.ap(wrapped_funcs)

    def __or__[B](self, f: Callable[[A], Monad[Lazy, B]]) -> Lazy[B]:
        """Infix operator for monadic bind (``|``).

        Args:
            f: A function that takes the resolved value and returns a
                ``Lazy[B]``.

        Returns:
            The Lazy returned by ``f`` after resolving this Lazy.
        """
        return self.bind(f)

    def __rshift__[B](self, other: Monad[Lazy, B]) -> Lazy[B]:
        """Infix operator for sequencing (``>>``).

        Discards the result of this Lazy and returns ``other``.

        Args:
            other: The Lazy to return after this one resolves.

        Returns:
            ``other``, ignoring the value of this Lazy.
        """
        return super().__rshift__(other)  # type: ignore

    def __repr__(self) -> str:
        """Return the string representation of this Lazy.

        Returns:
            A string of the form ``Lazy(<fetcher>)``.
        """
        return f"Lazy({self._fetcher})"
