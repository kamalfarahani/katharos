<p align="center">
  <img src="./logo.png" alt="Katharos logo" width="200">
</p>

<h1 align="center">Katharos</h1>

<p align="center">
  A functional programming and concurrency library for Python. Katharos pairs algebraic abstractions (<code>Functor</code>, <code>Applicative</code>, <code>Monad</code>, <code>Semigroup</code>, <code>Monoid</code>) and concrete types like <code>Maybe</code>, <code>Result</code>, <code>ImmutableList</code>, and <code>IO</code> with message-passing concurrency built on the same functional core. The two halves share one idea: model errors, effects, and concurrent communication as <strong>composable, type-safe values</strong>. A concurrent hand-off returns a <code>Result</code>, so "the channel closed" is something you handle, not an exception you catch.
</p>

<p align="center">
  <a href="https://pypi.org/project/katharos/"><img src="https://img.shields.io/pypi/v/katharos" alt="PyPI"></a>
  <a href="https://katharos.readthedocs.io/en/latest/"><img src="https://img.shields.io/readthedocs/katharos" alt="Docs"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/license-MIT-blue" alt="License"></a>
  <img src="https://img.shields.io/badge/coverage-94%25-brightgreen" alt="Coverage">
</p>

---

## Installation

```bash
pip install katharos
```

Or using `uv`:

```bash
uv add katharos
```

## Goals

Katharos exists to make functional-style Python practical, safe, and pleasant to write.

- **Errors, absence, and effects as values.** `Maybe`, `Result`, `IO`, and `Lazy` put failure, missing data, and side effects in the type signature, where they compose, instead of hiding them in `None` and exceptions.
- **Law-abiding abstractions.** `Functor`, `Applicative`, `Monad`, `Semigroup`, and `Monoid` come with their algebraic laws, checked by property-based tests (Hypothesis), so you can rely on them when you refactor.
- **Pythonic ergonomics.** Operators (`|`, `**`, `>>`, `@`) and `do`-notation keep functional code readable to Python developers. Everything is fully type-annotated and checked with pyright.
- **Concurrency on the same core.** Go-style CSP (`go`, `Channel`) returns `Result` values, so a closed or timed-out channel is something you handle, not an exception you catch.
- **Approachable.** Tutorials come first, so you can learn one concept at a time by building something useful.

### Non-goals

- Not a port of the full Haskell or Scala typeclass ecosystem. Katharos covers a small, well-tested set of abstractions.
- Not a replacement for `asyncio`. The concurrency layer is thread-based message passing.

## What it looks like

Two everyday problems, each shown without and with Katharos.

### Missing values: `Maybe`

Without Katharos, every lookup needs its own `None` check:

```python
def lookup_discount(user_id: int) -> float | None:
    user = find_user(user_id)
    if user is None:
        return None
    return find_discount(user)
```

With Katharos, `find_user` and `find_discount` return a `Maybe`, and `do`-notation short-circuits on `Nothing`:

```python
from katharos.types import Maybe
from katharos.syntax_sugar import do, DoBlock

def find_user(user_id: int) -> Maybe[User]: ...      # Just(user) or Nothing()
def find_discount(user: User) -> Maybe[float]: ...   # Just(0.15) or Nothing()

@do(Maybe)
def lookup_discount(user_id: int) -> DoBlock[Maybe, float]:
    user     = yield find_user(user_id)
    discount = yield find_discount(user)
    return discount                           # Just(0.15) or Nothing()
```

### Failures: `Result`

Without Katharos, each step can raise, so callers must know which exceptions to catch:

```python
def process(raw: str) -> int:
    n = int(raw)                              # may raise ValueError
    if n <= 0:
        raise ValueError(f"{n} is not positive")
    return n
```

With Katharos, failure is part of the return type, and steps chain with `|`:

```python
from katharos.types import Result

def parse_int(s: str) -> Result[ValueError, int]: ...        # Success(n) or Failure(ValueError)
def validate_positive(n: int) -> Result[ValueError, int]: ...  # Success(n) or Failure(ValueError)

def process(raw: str) -> Result[ValueError, int]:
    return parse_int(raw) | validate_positive   # a Failure short-circuits the chain
```

## Tour

### Chaining with `|` and `fmap`

`|` (bind) feeds a value into the next step; `fmap` transforms the value inside without changing the context:

```python
from katharos.types import Maybe

Maybe[int].Just(5) | (lambda x: Maybe[int].Just(x * 2))    # Just(10)
Maybe[int].Nothing() | (lambda x: Maybe[int].Just(x * 2))  # Nothing()
```

### Turning exceptions into values: `Result.catch`

`Result.catch` turns a function that raises into one that returns a `Result`, with no
manual `try/except`. Only the declared exception type becomes a `Failure`; the
caught exception keeps its traceback, so you can still find the line that failed.

```python
import traceback
from katharos.types import Result

@Result.catch(ValueError)
def parse_int(s: str) -> int:
    return int(s)

parse_int("42")    # Success(42)
parse_int("??")    # Failure(ValueError("invalid literal for int() with base 10: '??'"))

parse_int("42").fmap(lambda n: n * 2)   # Success(84)
parse_int("??").fmap(lambda n: n * 2)   # Failure(ValueError(...)), fmap is skipped

failure = parse_int("??")
if failure.is_failure():
    traceback.print_exception(failure.error)  # full traceback, pointing at the failing line
```

### Combining with `@`

The Semigroup operator combines two values of the same type:

```python
from katharos.types import ImmutableList

ImmutableList([1, 2]) @ ImmutableList([3, 4])  # ImmutableList([1, 2, 3, 4])
```

## Do-notation

`do`-notation works with any monad: `Maybe`, `Result`, `IO`, `ImmutableList` and your custom monads. Each `yield` unwraps the monadic value:

```python
from katharos.syntax_sugar import do, DoBlock
from katharos.types import Result

def parse_positive(x: int) -> Result[ValueError, int]:
    return Result.Success(x) if x > 0 else Result.Failure(ValueError(f"{x} is not positive"))

# Clean, imperative-style monadic code
@do(Result)
def do_block() -> DoBlock[Result, int]:
    x: int = yield parse_positive(5)
    y: int = yield parse_positive(3)
    return x + y

print(do_block())  # Success(8)
```

## Concurrency

Katharos provides **message-passing concurrency** that builds on the same functional core, with room for more than one concurrency model. The first model available is **Go-style CSP**: launch work concurrently with `go` (like Go's `go f(x)`), communicate over typed `Channel`s, and (crucially) receive values as a `Result`, so a closed or timed-out channel is a value you pattern-match, not an exception you wrap in `try`:

```python
from katharos.concurrency.csp import csp

ch = csp.Channel[int](capacity=1)

csp.go(ch.send, 42)     # run work concurrently, like Go's `go f(x)`

ch.recv()               # Success(42)

ch.close()
ch.recv()               # Failure(ChannelClosedError(...)): closure is a value, not a raise
```

Used as a context manager, `go` becomes a **structured-concurrency scope** that joins everything spawned inside it before the block exits:

```python
from katharos.concurrency.csp import csp

with csp.go:                 # scope waits for all work launched inside
    csp.go(worker, 1)
    csp.go(worker, 2)
# both workers have finished here
```

Here is the Fibonacci example from the [Go Tour](https://go.dev/tour/concurrency/4): a producer sends values and closes the channel, and the consumer ranges over it until it is closed.

```python
from katharos.concurrency.csp import Channel, csp


def fibonacci(n: int, c: Channel[int]) -> None:
    x, y = 0, 1
    for _ in range(n):
        c.send(x)
        x, y = y, x + y
    c.close()


c = csp.Channel[int](capacity=10)
csp.go(fibonacci, 10, c)

for i in c:  # receives until the channel is closed
    print(i)  # 0 1 1 2 3 5 8 13 21 34

print(c.recv())  # Failure(ChannelClosedError(...)): closure is a value, not a raise
```

Every concurrency model is bound to a swappable `BaseThreadingBackend` (standard threads by default), and the `csp` runtime supplies it automatically, so you can retarget work onto a different backend in one place. Additional models (such as an actor model) are planned, built on the same backend abstraction and the same `Result`-valued, composable style.

## Documentation

Full tutorials, how-to guides, API reference, and explanations of the mathematical foundations are at **[katharos.readthedocs.io](https://katharos.readthedocs.io/en/latest/)**.

## License

MIT
