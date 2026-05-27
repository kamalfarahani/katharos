"""Katharos: A functional programming library for Python.

Katharos provides algebraic abstractions like Semigroups, Monoids, Functors,
Applicatives, and Monads, along with immutable data structures to enable
composable, type-safe, and side-effect-free code.

Main modules:
    - :mod:`katharos.algebra`: Core algebraic abstractions (Functor, Applicative, Monad, etc.)
    - :mod:`katharos.types`: Concrete implementations (Maybe, Result, ImmutableList, IO)
    - :mod:`katharos.functools`: Functional utilities (compose, fold, curry, etc.)
    - :mod:`katharos.syntax_sugar`: Syntactic conveniences (Do-notation)

Example:
    >>> from katharos.types import Maybe
    >>> result = Maybe.Just(5).fmap(lambda x: x * 2)
    >>> result
    Just(10)
"""
