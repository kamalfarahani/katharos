# Katharos

Katharos is a functional programming library for Python that provides algebraic abstractions like Semigroups, Monoids, Functors, Applicatives, and Monads, along with immutable data structures to enable composable, type-safe, and side-effect-free code.

<img src="./logo.png" alt="logo" width="300" height="300">

## Installation

```bash
pip install katharos
```

## Quick Start

```python
from katharos.types import Maybe

# Safe optional value handling
result = Maybe.Just(5).fmap(lambda x: x * 2)
print(result)  # Just(10)

# Automatic short-circuiting
nothing = Maybe.Nothing().fmap(lambda x: x * 2)
print(nothing)  # Nothing()
```

See the [Getting Started tutorial](docs/tutorials/getting-started.rst) for more examples.

## License

MIT License