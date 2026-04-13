from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from katharos.algebra import Monad


@dataclass
class DoVariable:
    """
    A placeholder representing a bound monadic value in a Do block.

    Attributes:
        index: The registration order of this variable within the Do block.
        monad: The monad whose value will be extracted during evaluation.
    """

    index: int
    monad: Monad


class Do:
    """
    A context manager that provides Haskell-style do-notation for Monads.

    Do-notation is syntactic sugar for sequencing monadic computations via
    `bind`. Instead of chaining `.bind()` calls manually, `Do` lets you
    register monads with `arrow` and then resolve all bound values at once
    with `eval`, which builds the equivalent nested `bind` chain internally.

    The equivalent Haskell do-block:

        do
            x_1 <- m_1
            x_2 <- m_2
            f x_1 x_2

    Is expressed in Python as:

        with Do() as do:
            x_1 = do.arrow(m_1)
            x_2 = do.arrow(m_2)
            result = do.eval(f, x_1=x_1, x_2=x_2)

    Examples:
        Short-circuit on Nothing propagates correctly:

            >>> from katharos.ds.maybe.maybe import Maybe
            >>> m_1 = Maybe.Just(3)
            >>> m_2 = Maybe.Nothing()
            >>> with Do() as do:
            ...     x_1 = do.arrow(m_1)
            ...     x_2 = do.arrow(m_2)
            ...     result = do.eval(lambda x_1, x_2: Maybe.Just(x_1 + x_2), x_1=x_1, x_2=x_2)
            >>> result
            Nothing()

        Both values present — computation runs to completion:

            >>> m_1 = Maybe.Just(3)
            >>> m_2 = Maybe.Just(4)
            >>> with Do() as do:
            ...     x_1 = do.arrow(m_1)
            ...     x_2 = do.arrow(m_2)
            ...     result = do.eval(lambda x_1, x_2: Maybe.Just(x_1 + x_2), x_1=x_1, x_2=x_2)
            >>> result
            Just(7)

    Note:
        `_vars` is cleared automatically when the `with` block exits.
    """

    def __init__(self) -> None:
        self._vars: list[DoVariable] = []

    def __enter__(self) -> Do:
        """
        Enter the do-notation context.

        Returns:
            Do: This ``Do`` instance, bound to the ``as`` target.
        """
        return self

    def __exit__(self, *args: object) -> None:
        """
        Exit the do-notation context, clearing all registered variables.

        Args:
            *args: Exception info (type, value, traceback); unused.
        """
        self._vars.clear()

    def arrow(self, monad: Monad) -> DoVariable:
        """
        Register a monad for binding and return a `DoVariable` placeholder.

        Corresponds to the `<-` arrow in Haskell do-notation. The returned
        `DoVariable` must be passed to `eval` as a keyword argument to
        receive the value extracted from the monad.

        Args:
            monad: The monad whose inner value will be bound.

        Returns:
            A placeholder carrying the monad and its registration index,
            to be passed as a keyword argument to `eval`.
        """

        var = DoVariable(
            index=len(self._vars),
            monad=monad,
        )
        self._vars.append(var)

        return var

    def eval(
        self,
        f: Callable[..., Monad],
        **vars: DoVariable,
    ) -> Monad:
        """
        Resolve all registered monads and apply `f` to the extracted values.

        Builds a nested `bind` chain over the provided `DoVariable` instances in
        their registration order (determined by `DoVariable.index`), then
        calls `f` with the bound values as keyword arguments.

        This is equivalent to the following Haskell expression:

            m_1 >>= (x_1 -> m_2 >>= (x_2 -> f x_1 x_2))

        Args:
            f: A function accepting the extracted values as keyword arguments
                and returning a monad of the same type.
            **vars: Keyword-argument mapping of name to `DoVariable`.
                Each name becomes the parameter name passed to `f`.

        Returns:
            The result of the fully sequenced monadic computation.

        Raises:
            ValueError: If a provided `DoVariable` was not registered via
                `arrow` in this `Do` block.
        """

        for var in vars.values():
            if var not in self._vars:
                raise ValueError(f"Variable {var} not found in do block")

        ordered = sorted(vars.items(), key=lambda item: item[1].index)
        names = [name for name, _ in ordered]
        monads = [var.monad for _, var in ordered]

        def chain(index: int, bound: dict) -> Monad:
            if index == len(monads):
                return f(**{name: bound[name] for name in names})
            return monads[index].bind(
                lambda value, i=index: chain(i + 1, {**bound, names[i]: value})
            )

        return chain(0, {})
