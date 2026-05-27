"""Syntactic sugar for monadic operations.

This module provides convenient syntax for working with monads, making
monadic code more readable and maintainable.

The :func:`do` decorator provides Haskell-style do-notation for sequencing
monadic computations using generator functions.
"""

from .do import DoBlock, do

__all__ = [
    "do",
    "DoBlock",
]
