from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from katharos.algebra import Monad
from katharos.functools import F


@dataclass
class DoVariable[M: Monad]:
    """
    A placeholder representing a bound monadic value in a Do block.

    Attributes:
        index: The registration order of this variable within the Do block.
        monad: The monad whose value will be extracted during evaluation.
    """

    def __hash__(self) -> int:
        return hash(self.index)

    def __eq__(self, other: object, /) -> bool:
        if not isinstance(other, DoVariable):
            return False
        return self.index == other.index

    index: int
    monad: M


class Do[M: Monad]:
    """Context manager providing Haskell-style do-notation for monadic computations.

    ``Do[M]`` allows sequencing monadic values in an imperative style by
    transparently threading ``bind`` chains through registered variables.
    Bind a monad to a variable with :meth:`arrow` (analogous to ``<-`` in
    Haskell), then produce a final monadic result with :meth:`ret` (plain
    return value) or :meth:`eval` (already-monadic return value).

    The monad type must be supplied as a type parameter via ``Do[M]``, which
    returns a specialised subclass with ``_monad_type`` set.

    Type Args:
        M: The :class:`~katharos.algebra.Monad` subtype that all values in
            this block belong to.

    Attributes:
        _monad_type: The concrete :class:`~katharos.algebra.Monad` subclass
            bound to this Do block, or ``None`` if the class has not been
            specialised with a type parameter.

    Examples:
        Basic usage with the ``Maybe`` monad::

            m1 = Maybe[int].Just(3)
            m2 = Maybe[int].Just(4)

            with Do[Maybe]() as do:
                x1 = do.arrow(m1)
                x2 = do.arrow(m2)
                result: Maybe[int] = do.ret(
                    lambda x1, x2: x1 + x2,
                    x1=x1,
                    x2=x2,
                )
            # result == Maybe.Just(7)

        Short-circuit behavior when a ``Nothing`` is encountered::

            m1 = Maybe[int].Just(3)
            m2 = Maybe[int].Nothing()

            with Do[Maybe]() as do:
                x1 = do.arrow(m1)
                x2 = do.arrow(m2)
                result: Maybe[int] = do.ret(
                    lambda x1, x2: x1 + x2,
                    x1=x1,
                    x2=x2,
                )
            # result == Maybe.Nothing()
    """

    _monad_type: type[M] | None = None

    def __class_getitem__(cls, params):
        """Return a subclass of ``Do`` with ``_monad_type`` bound to *params*.

        Called implicitly by the ``Do[M]`` subscription syntax.  When multiple
        type arguments are given (as a tuple) only the first element is used as
        the monad type.

        Args:
            params: A single monad type, or a tuple whose first element is the
                monad type when additional type arguments are provided.

        Returns:
            A new subclass of this class whose ``_monad_type`` class attribute
            is set to the resolved monad type.  The subclass inherits the same
            ``__name__`` and ``__qualname__`` as the parent so that it is
            transparent to users.
        """
        monad_type = params[0] if isinstance(params, tuple) else params

        class _BoundDo(cls):
            _monad_type = monad_type

        _BoundDo.__name__ = cls.__name__
        _BoundDo.__qualname__ = cls.__qualname__
        return _BoundDo

    def __init__(self) -> None:
        """Initialise an empty Do block with no registered variables."""
        self._vars: list[DoVariable[M]] = []

    def __enter__(self) -> Do[M]:
        """Enter the Do block context and return this instance.

        Returns:
            This ``Do`` instance, allowing the ``with Do[M]() as do:`` pattern.
        """
        return self

    def __exit__(self, *args: object) -> None:
        """Exit the Do block context and release all registered variables.

        Clears the internal variable registry so that the same ``Do`` instance
        cannot be accidentally reused after the ``with`` block ends.

        Args:
            *args: Exception info forwarded by the context-manager protocol
                (``exc_type``, ``exc_val``, ``exc_tb``); ignored.
        """
        self._vars.clear()

    def arrow(self, monad: M) -> DoVariable[M]:
        """Register a monadic value and return a placeholder variable.

        Analogous to the ``<-`` arrow in Haskell do-notation.  The returned
        :class:`DoVariable` can be passed as a keyword argument to
        :meth:`ret` or :meth:`eval` so that the unwrapped value is forwarded
        to the final function.

        Args:
            monad: A monadic value of type ``M`` whose inner value should be
                extracted during evaluation.

        Returns:
            A :class:`DoVariable` placeholder that records the position of
            *monad* in the bind chain.
        """
        var = DoVariable(
            index=len(self._vars),
            monad=monad,
        )
        self._vars.append(var)

        return var

    def eval(
        self,
        f: Callable[..., M],
        **vars: DoVariable[M],
    ) -> M:
        for var in vars.values():
            if var not in self._vars:
                raise ValueError(f"Variable {var} not found in do block")

        def chain(index: int, bound: dict) -> M:
            if index == len(self._vars):
                return f(**bound)

            if self._vars[index] in vars.values():
                name = next(n for n, v in vars.items() if v == self._vars[index])

                def bind_value(value: object) -> M:
                    return chain(
                        index + 1,
                        {**bound, name: value},
                    )

                return self._vars[index].monad | bind_value  # type: ignore
            else:

                def dummy_bind(value: object) -> M:
                    return chain(index + 1, bound)

                return self._vars[index].monad | dummy_bind  # type: ignore

        return chain(0, {})

    def ret(
        self,
        f: Callable[..., object],
        **vars: DoVariable[M],
    ) -> M:
        """Evaluate a plain function and lift its result into the monad.

        Behaves identically to :meth:`eval`, except that *f* returns a plain
        (non-monadic) value which is automatically wrapped via
        ``monad_type.ret()`` before being threaded through the bind chain.
        This is the most common entry-point for finalising a do-block.

        Args:
            f: A callable that accepts the unwrapped values of the variables
                listed in *vars* and returns a plain (non-monadic) value.  The
                return value is lifted into ``M`` via ``monad_type.ret()``.
            **vars: Keyword-argument mapping of parameter names to
                :class:`DoVariable` placeholders previously obtained from
                :meth:`arrow`.  Each key becomes the parameter name passed to
                *f* when the bind chain resolves.

        Returns:
            The final monadic value ``M`` produced by chaining all registered
            monads through ``bind``, applying *f* to the extracted values, and
            wrapping the result with ``monad_type.ret()``.

        Raises:
            AssertionError: If the Do block was not specialised with a type
                parameter (i.e. ``_monad_type`` is ``None``).
        """
        monad_type = self._monad_type
        assert monad_type is not None, (
            "Do must be instantiated with a type parameter: Do[M, A]()"
        )

        def f_m(*args, **kwargs) -> M:
            return monad_type.ret(f(*args, **kwargs))  # type: ignore

        return self.eval(f_m, **vars)
