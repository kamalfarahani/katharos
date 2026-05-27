"""Algebraic abstractions for functional programming.

This module provides the core algebraic type classes that form the foundation
of functional programming in Katharos. These abstractions follow mathematical
laws and enable composable, predictable code.

The hierarchy of abstractions (from least to most powerful):
    - :class:`Semigroup`: Types with an associative binary operation
    - :class:`Monoid`: Semigroups with an identity element
    - :class:`Functor`: Types that can be mapped over
    - :class:`Applicative`: Functors with function application
    - :class:`Monad`: Applicatives with sequencing capabilities

Each abstraction builds upon the previous one, adding more structure and
capabilities while maintaining the laws of the simpler abstractions.
"""

from .applicative import Applicative
from .functor import Functor
from .monad import Monad
from .monoid import Monoid
from .semigroup import Semigroup

__all__ = [
    "Applicative",
    "Functor",
    "Monad",
    "Monoid",
    "Semigroup",
]
