from __future__ import annotations

from collections.abc import Callable, Generator
from typing import Any

from katharos.algebra import Monad

type DoBlock[R] = Generator[Any, Any, R]
"""Generator type for use with the :func:`do` decorator.

``R`` is the plain return type of the block. Yield expressions evaluate to
``Any`` because Python's ``Generator`` has a single ``SendType`` for the
entire function; per-yield type inference across different inner types is not
expressible without a type-checker plugin. Annotate individual bindings
inline instead::

    @do(Maybe)
    def computation() -> DoBlock[int]:
        x: int = yield Maybe.Just(3)
        y: str = yield Maybe.Just("hi")
        return x + len(y)

Note:
    Because Python lacks higher-kinded types, the decorated function's return
    type is inferred as ``M`` (e.g. ``Maybe``) rather than ``M[R]``
    (e.g. ``Maybe[int]``).
"""


def do[M: Monad, R](
    monad_type: type[M],
) -> Callable[[Callable[..., DoBlock[R]]], Callable[..., M]]:
    """Decorator for generator-based do-notation.

    Each ``yield monad`` extracts the wrapped value, analogous to ``<-`` in
    Haskell. The unwrapped value is immediately available for use in subsequent
    yields. Annotate the generator with :data:`DoBlock[R]` where ``R`` is the
    plain return type, lifted via ``monad_type.ret()`` at the end of the block.
    Annotate individual yield sites inline for per-binding types::

        x: int = yield Maybe.Just(3)
        y: str = yield Maybe.Just("hi")

    Short-circuiting is handled transparently by ``bind``: if any yielded monad
    is ``Nothing`` or ``Failure``, the rest of the generator is abandoned and
    that monad is returned immediately.

    Works correctly with non-deterministic monads such as ``ImmutableList``
    whose ``bind`` calls its function more than once. Each branch replays the
    generator from the start with the accumulated history of sent values, so
    every execution path sees a fresh generator in the right state.

    Note:
        Side effects in the generator body (between ``yield`` expressions) will
        be replayed once per branch. Keep the generator body pure; place any
        side effects inside the yielded monads themselves.

    Args:
        monad_type: The concrete monad class (e.g. ``Maybe``, ``Result``).

    Returns:
        A decorator that transforms a generator function into an ordinary
        function returning a value of type ``M``.

    Examples:
        >>> from katharos.types import Maybe
        >>> @do(Maybe)
        ... def computation() -> DoBlock[int]:
        ...     x: int = yield Maybe.Just(3)
        ...     y: int = yield Maybe.Just(x + 1)  # x is 3 here
        ...     return x + y
        >>> computation()
        Just(7)

        >>> @do(Maybe)
        ... def short_circuit() -> DoBlock[int]:
        ...     x: int = yield Maybe.Just(10)
        ...     y: int = yield Maybe.Nothing()    # stops here
        ...     return x + y                      # never reached
        >>> short_circuit()
        Nothing()
    """

    def decorator(f: Callable[..., DoBlock[R]]) -> Callable[..., M]:
        def wrapper(*args: Any, **kwargs: Any) -> M:
            def step(history: tuple) -> M:
                gen = f(*args, **kwargs)
                try:
                    monad = next(gen)
                    for value in history:
                        monad = gen.send(value)
                except StopIteration as e:
                    result = e.value
                    return monad_type.ret(result)  # type: ignore[return-value]

                return monad.bind(  # type: ignore[return-value]
                    lambda value, h=history: step(h + (value,))
                )

            return step(())

        return wrapper

    return decorator
