<p align="center">
  <img src="./logo.png" alt="Katharos logo" width="200">
</p>

<h1 align="center">Katharos</h1>

<p align="center">
  Functional programming abstractions for Python — Monads, Applicatives, Functors, and immutable data structures for composable, type-safe code.
</p>

<p align="center">
  <a href="https://pypi.org/project/katharos/"><img src="https://img.shields.io/pypi/v/katharos" alt="PyPI"></a>
  <a href="https://katharos.readthedocs.io/en/latest/"><img src="https://img.shields.io/readthedocs/katharos" alt="Docs"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/license-MIT-blue" alt="License"></a>
  <img src="https://img.shields.io/pypi/pyversions/katharos" alt="Python versions">
</p>

---

## Installation

```bash
pip install katharos
```

## Quick Start

**Handle optional values without `None` checks:**

```python
from katharos.types import Maybe

result = Maybe.Just(5) | (lambda x: Maybe.Just(x * 2))  # Just(10)
nothing = Maybe.Nothing() | (lambda x: Maybe.Just(x * 2))  # Nothing()
```

**Model errors as values instead of exceptions:**

```python
from katharos.types import Result

def parse_int(s: str) -> Result[ValueError, int]:
    try:
        return Result.Success(int(s))
    except ValueError as e:
        return Result.Failure(e)

parse_int("42") | (lambda n: Result.Success(n * 2))  # Success(84)
parse_int("??") | (lambda n: Result.Success(n * 2))  # Failure(...)
```

**Chain operations with do-notation:**

```python
from katharos.types import Maybe
from katharos.syntax_sugar import do, DoBlock

@do(Maybe)
def lookup_discount(user_id: int) -> DoBlock[float]:
    user    = yield find_user(user_id)      # short-circuits on Nothing
    account = yield find_account(user)
    return account.discount

lookup_discount(42)  # Just(0.15) or Nothing()
```

**Combine values with the Semigroup operator:**

```python
from katharos.types import ImmutableList

ImmutableList([1, 2]) @ ImmutableList([3, 4])  # ImmutableList([1, 2, 3, 4])
```

## Documentation

Full tutorials, how-to guides, API reference, and explanations of the mathematical foundations are at **[katharos.readthedocs.io](https://katharos.readthedocs.io/en/latest/)**.

## License

MIT
