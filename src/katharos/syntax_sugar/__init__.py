"""Syntactic sugar for monadic operations.

This module provides convenient syntax for working with monads, making
monadic code more readable and maintainable.

The :class:`Do` context manager provides Haskell-style do-notation for
sequencing monadic computations in an imperative style.
"""

from .do import Do

__all__ = [
    "Do",
]
