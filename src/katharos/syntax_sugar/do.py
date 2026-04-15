from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from katharos.algebra import Monad


@dataclass
class DoVariable[M, A]:
    """
    A placeholder representing a bound monadic value in a Do block.

    Attributes:
        index: The registration order of this variable within the Do block.
        monad: The monad whose value will be extracted during evaluation.
    """

    index: int
    monad: Monad[M, A]


class Do[M, A]:
    """A context manager providing Haskell-style do-notation for Monads.

    Do-notation is syntactic sugar for sequencing monadic computations via
    `bind`. Instead of chaining `.bind()` calls manually, `Do` lets you
    register monads with `arrow` and then resolve all bound values at once
    with `eval` (returning a monad) or `ret` (returning a lifted pure value).

    The type parameter ``M`` must be supplied at instantiation time via
    ``Do[M, A]()``. The concrete monad class ``M`` is captured and stored as
    `_monad_type`, making it available to `ret` for calling ``M.ret``.

    The equivalent Haskell do-block::

        do
            x_1 <- m_1
            x_2 <- m_2
            f x_1 x_2

    Is expressed in Python as::

        with Do[M, A]() as do:
            x_1 = do.arrow(m_1)
            x_2 = do.arrow(m_2)
            result = do.eval(f, x_1=x_1, x_2=x_2)

    Type Args:
        M: The monad constructor (e.g. ``Maybe``). Must be a concrete subclass
            of ``Monad`` and is captured at subscript time via
            ``__class_getitem__``.
        A: The inner value type carried by the monad.

    Attributes:
        _monad_type (type[Monad] | None): The concrete monad class ``M``
            captured when the class is subscripted as ``Do[M, A]``. ``None``
            when ``Do`` is used without type parameters.

    Examples:
        Short-circuit on Nothing propagates correctly:

            >>> from katharos.ds.maybe.maybe import Maybe
            >>> m_1 = Maybe.Just(3)
            >>> m_2 = Maybe.Nothing()
            >>> with Do[Maybe, int]() as do:
            ...     x_1 = do.arrow(m_1)
            ...     x_2 = do.arrow(m_2)
            ...     result = do.eval(lambda x_1, x_2: Maybe.Just(x_1 + x_2), x_1=x_1, x_2=x_2)
            >>> result
            Nothing()

        Both values present — computation runs to completion:

            >>> m_1 = Maybe.Just(3)
            >>> m_2 = Maybe.Just(4)
            >>> with Do[Maybe, int]() as do:
            ...     x_1 = do.arrow(m_1)
            ...     x_2 = do.arrow(m_2)
            ...     result = do.ret(lambda x_1, x_2: x_1 + x_2, x_1=x_1, x_2=x_2)
            >>> result
            Just(7)

    Note:
        `_vars` is cleared automatically when the ``with`` block exits.
    """

    _monad_type: type[Monad] | None = None

    def __class_getitem__(cls, params):
        monad_type = params[0] if isinstance(params, tuple) else params

        class _BoundDo(cls):
            _monad_type = monad_type

        _BoundDo.__name__ = cls.__name__
        _BoundDo.__qualname__ = cls.__qualname__
        return _BoundDo

    def __init__(self) -> None:
        self._vars: list[DoVariable[M, A]] = []

    def __enter__(self) -> Do[M, A]:
        """Enter the do-notation context.

        Returns:
            This ``Do`` instance, bound to the ``as`` target.
        """
        return self

    def __exit__(self, *args: object) -> None:
        """Exit the do-notation context, clearing all registered variables.

        Args:
            *args: Exception info (type, value, traceback); unused.
        """
        self._vars.clear()

    def arrow(self, monad: Monad[M, A]) -> DoVariable[M, A]:
        """Register a monad for binding and return a `DoVariable` placeholder.

        Corresponds to the ``<-`` arrow in Haskell do-notation. The returned
        `DoVariable` must be passed to `eval` or `ret` as a keyword argument
        to receive the value extracted from the monad.

        Args:
            monad: The monad whose inner value will be bound.

        Returns:
            A `DoVariable` carrying the monad and its registration index,
            to be passed as a keyword argument to `eval` or `ret`.
        """

        var = DoVariable(
            index=len(self._vars),
            monad=monad,
        )
        self._vars.append(var)

        return var

    def eval(
        self,
        f: Callable[..., Monad[M, A]],
        **vars: DoVariable[M, A],
    ) -> Monad[M, A]:
        """Resolve all registered monads and apply ``f`` to the extracted values.

        Builds a nested ``bind`` chain over the provided `DoVariable` instances
        in their registration order (determined by `DoVariable.index`), then
        calls ``f`` with the bound values as keyword arguments. ``f`` must
        itself return a monad; use `ret` instead when ``f`` returns a plain
        value.

        Equivalent Haskell expression::

            m_1 >>= (λx_1 -> m_2 >>= (λx_2 -> f x_1 x_2))

        Args:
            f: A callable accepting the extracted values as keyword arguments
                and returning a ``Monad[M, A]``.
            **vars: Keyword-argument mapping of name to `DoVariable`.
                Each name becomes the parameter name passed to ``f``.

        Returns:
            The result of the fully sequenced monadic computation.

        Raises:
            ValueError: If a provided `DoVariable` was not registered via
                `arrow` in this ``Do`` block.
        """
        for var in vars.values():
            if var not in self._vars:
                raise ValueError(f"Variable {var} not found in do block")

        ordered = sorted(vars.items(), key=lambda item: item[1].index)
        names = [name for name, _ in ordered]
        monads = [var.monad for _, var in ordered]

        def chain(index: int, bound: dict) -> Monad[M, A]:
            if index == len(monads):
                return f(**{name: bound[name] for name in names})
            return monads[index].bind(
                lambda value, i=index: chain(i + 1, {**bound, names[i]: value})
            )

        return chain(0, {})

    def ret(
        self,
        f: Callable[..., A],
        **vars: DoVariable[M, A],
    ) -> Monad[M, A]:
        """Resolve all registered monads, apply ``f``, and lift the result.

        Like `eval`, but ``f`` returns a plain value of type ``A`` instead of
        a monad. The result is automatically lifted into ``M`` via
        ``M.ret``, where ``M`` is the monad class captured from the
        ``Do[M, A]`` subscript.

        Equivalent Haskell expression::

            m_1 >>= (λx_1 -> m_2 >>= (λx_2 -> return (f x_1 x_2)))

        Args:
            f: A callable accepting the extracted values as keyword arguments
                and returning a plain value of type ``A``.
            **vars: Keyword-argument mapping of name to `DoVariable`.
                Each name becomes the parameter name passed to ``f``.

        Returns:
            The result of the fully sequenced monadic computation, with
            the return value of ``f`` lifted into ``M``.

        Raises:
            AssertionError: If ``Do`` was instantiated without a type
                parameter (i.e. ``_monad_type`` is ``None``).
            ValueError: If a provided `DoVariable` was not registered via
                `arrow` in this ``Do`` block.
        """
        monad_type = self._monad_type
        assert monad_type is not None, (
            "Do must be instantiated with a type parameter: Do[M, A]()"
        )

        def f_m(*args, **kwargs) -> Monad[M, A]:
            return monad_type.ret(f(*args, **kwargs))

        return self.eval(f_m, **vars)
