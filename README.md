<p align="center">
  <img src="./logo.png" alt="Katharos logo" width="200">
</p>

<h1 align="center">Katharos</h1>

<p align="center">
  A functional programming library for Python. Katharos brings algebraic abstractions — <code>Functor</code>, <code>Applicative</code>, <code>Monad</code>, <code>Semigroup</code>, <code>Monoid</code> — together with concrete types like <code>Maybe</code>, <code>Result</code>, <code>ImmutableList</code>, and <code>IO</code>, so you can model effects, errors, and data transformations as composable, type-safe pipelines.
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

Or using `uv`

```bash
uv add katharos
```

## What it looks like

**Before** — scattered `None` checks and exception handling:

```python
user = find_user(user_id)
if user is None:
    return None
account = find_account(user)
if account is None:
    return None
return account.discount
```

**After** — `do`-notation that short-circuits cleanly on `Nothing`:

```python
from katharos.types import Maybe
from katharos.syntax_sugar import do, DoBlock

@do(Maybe)
def lookup_discount(user_id: int) -> DoBlock[float]:
    user    = yield find_user(user_id)
    account = yield find_account(user)
    return account.discount   # Just(0.15) or Nothing()
```

**Before** — nested try/except to propagate errors:

```python
def process(raw: str) -> int:
    try:
        n = parse_int(raw)
    except ValueError as e:
        raise RuntimeError("bad input") from e
    try:
        return validate_positive(n)
    except ValueError as e:
        raise RuntimeError("bad value") from e
```

**After** — errors as values, chained with `|`:

```python
from katharos.types import Result

def process(raw: str) -> Result[Exception, int]:
    return parse_int(raw) | validate_positive   # Failure short-circuits automatically
```

## More examples

**Handle optional values without `None` checks:**

```python
from katharos.types import Maybe

result = Maybe[int].Just(5) | (lambda x: Maybe[int].Just(x * 2))  # Just(10)
nothing = Maybe[int].Nothing() | (lambda x: Maybe[int].Just(x * 2))  # Nothing()
```

**Model errors as values instead of exceptions:**

```python
from katharos.types import Result

def parse_int(s: str) -> Result[ValueError, int]:
    try:
        return Result.Success(int(s))
    except ValueError as e:
        return Result.Failure(e)

parse_int("42").fmap(lambda n: n * 2) # Success(84)
parse_int("??").fmap(lambda n: n * 2)  # Failure(...)
```

**Combine values with the Semigroup operator:**

```python
from katharos.types import ImmutableList

ImmutableList([1, 2]) @ ImmutableList([3, 4])  # ImmutableList([1, 2, 3, 4])
```

## Do-notation

`do`-notation works with any monad — `Maybe`, `Result`, `IO`, `ImmutableList` and your custom monads. Each `yield` unwraps the monadic value:

```python
from katharos.syntax_sugar import do, DoBlock
from katharos.types import Result

def parse_positive(x: int) -> Result[ValueError, int]:
    return Result.Success(x) if x > 0 else Result.Failure(ValueError(f"{x} is not positive"))

# Clean, imperative-style monadic code
@do(Result)
def do_block() -> DoBlock[int]:
    x: int = yield parse_positive(5)
    y: int = yield parse_positive(3)
    return x + y

print(do_block())  # Success(8)
```


## Documentation

Full tutorials, how-to guides, API reference, and explanations of the mathematical foundations are at **[katharos.readthedocs.io](https://katharos.readthedocs.io/en/latest/)**.

## License

MIT
