"""Concrete type implementations with algebraic properties.

This module provides immutable data structures that implement the algebraic
abstractions from :mod:`katharos.algebra`. These types enable type-safe,
composable functional programming patterns.

Available types:
    - :class:`Maybe`: Optional values without None checks
    - :class:`Result`: Error handling without exceptions
    - :class:`ImmutableList`: Immutable list with monadic operations
    - :class:`NonEmptyList`: List guaranteed to have at least one element
    - :class:`IO`: Lazy computation with side effects
    - :class:`MonoidMaybe`: Maybe with monoid instance
    - :class:`Lazy`: Lazy synchronous computation monad
    - :class:`UnwrapError`: Raised when extracting an absent value

Each type implements appropriate algebraic abstractions (Functor, Applicative,
Monad, etc.) and provides operators for convenient composition.
"""

from .errors import UnwrapError
from .lazy import Lazy
from .list import ImmutableList, NonEmptyList
from .maybe import Maybe, MonoidMaybe
from .result import Result
from .side_effect import IO

__all__ = [
    "ImmutableList",
    "NonEmptyList",
    "Maybe",
    "MonoidMaybe",
    "Lazy",
    "Result",
    "IO",
    "UnwrapError",
]
