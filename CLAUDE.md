# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run all tests with coverage (80% minimum required)
uv run pytest --cov=katharos --cov-fail-under=80

# Run a single test file
uv run pytest tests/types/maybe/test_maybe.py

# Run a specific test by name
uv run pytest -k "test_name"

# Lint
uv run ruff check src tests

# Format
uv run ruff format src tests

# Check formatting without modifying
uv run ruff format --check src tests

# Type check
uv run pyright src

# Multi-version test matrix (py313, py314, lint)
uv run tox

# Build docs
cd docs && make html
```

## Architecture

Katharos is a functional programming library structured in three layers, plus a concurrency module (`src/katharos/concurrency/`):

### Layer 1: Algebraic abstractions (`src/katharos/algebra/`)

Abstract base classes only — no concrete logic. Two independent hierarchies:

- **Combining**: `Semigroup` (associative `op`, exposed as `@`) → `Monoid` (adds `identity()` classmethod)
- **Computational context**: `Functor` (`fmap`) → `Applicative` (`pure`, `ap`, exposed as `**`) → `Monad` (`bind`, exposed as `|`; `then`/`>>` for sequencing)

### Layer 2: Concrete types (`src/katharos/types/`)

Each type implements the appropriate algebra interfaces:

| Type | Implements | State variants |
|------|-----------|----------------|
| `Maybe[A]` | Monad | `Just(value)` / `Nothing()` |
| `Result[E, A]` | Monad | `Success(value)` / `Failure(exc)` |
| `ImmutableList[T]` | Monad + Monoid | wraps a Python list, immutable |
| `NonEmptyList[T]` | Monad + Semigroup | guaranteed non-empty, has `.head` and `.tail` |
| `IO[A]` | Monad | lazy side-effect wrapper; call `.execute()` to run; wraps a `FunctionWithSideEffect` |
| `Lazy[A]` | Monad | lazy, memoized synchronous computation; call `.resolve()` to run (`src/katharos/types/lazy.py`) |
| `MonoidMaybe` | Monoid | Maybe with a monoid instance |
| `Sum`, `Product` | Monoid | numeric monoids; constrained by the `AdditiveMonoid`/`MultiplicativeMonoid` structural protocols (`src/katharos/types/monoid/`) |

`Maybe` and `Result` are `@final` — do not subclass. Use `is_just()`/`is_nothing()` and `is_success()`/`is_failure()` for state checks rather than type checks.

`Result`'s success/failure state is tracked internally, not inferred from the wrapped value's type — so an exception can be carried as a *success* value via `Success`/`pure` without being treated as a `Failure`. `Lazy` runs its fetcher at most once: `.resolve()` memoizes the value (and memoizes a raised exception, re-raising it on every later call); the guard lock is not reentrant, so a fetcher that resolves the same `Lazy` deadlocks.

### Layer 3: Utilities

- **`src/katharos/functools/f.py`** — `F` static namespace: `compose`, `id`, `foldr`, `foldl`, `sigma` (fold a `NonEmptyList[Semigroup]`), `curry`, `lift_a2`/`lift_a3` (lift a binary/ternary function into an `Applicative` context)
- **`src/katharos/syntax_sugar/do.py`** — `do` decorator for Haskell-style do-notation:
  ```python
  @do(Maybe)
  def computation() -> DoBlock[Maybe, int]:
      x: int = yield Maybe.Just(3)   # analogous to x <- Just 3 in Haskell
      y: int = yield Maybe.Just(4)
      return x + y
  ```
  Each `yield` unwraps the monadic value (short-circuits on `Nothing`/`Failure`). The plain `return` is automatically lifted via `Maybe.ret()`. The `DoBlock[M, R]` return-type alias (`Generator[M, Any, R]`) is exported alongside `do`.

### Concurrency (`src/katharos/concurrency/`)

Concurrency types are decoupled from any specific threading library by a backend abstraction. `BaseThreadingBackend` (in `base_threading_backend.py`) defines `spawn`, `create_lock`, `create_condition`, and `create_local` (context-local storage); `ThreadingBackend` is the standard-library default, returned by `default_backend()`. The `AbstractLock`/`AbstractCondition` protocols capture only the context-manager + wait/notify surface used, so `threading.Lock`/`threading.Condition` satisfy them structurally. A green-thread backend (e.g. greenlet/gevent) can be supplied instead. `Lazy` and `Channel` both accept an optional `backend=` and fall back to `default_backend()`.

CSP-style primitives live in `concurrency/csp/`:

- **`go`** (module-level `Go` instance) — launches `go(fn, *args, **kwargs)` concurrently, returning a thread handle (fire-and-forget; return value discarded, exceptions don't propagate out). Used as a context manager (`with go:`), it becomes a structured-concurrency scope that joins all work spawned inside it on exit. Scopes are tracked per execution context via the backend's context-local storage, so the shared `go` instance nests correctly.
- **`Channel[A]`** — Go-style thread-safe channel. `capacity=0` (default) is unbuffered (synchronous rendezvous); `capacity>0` buffers. `recv(timeout=None)` returns a `Result`: `Success(value)`, `Failure(ChannelClosedError)` when closed and drained, or `Failure(ChannelTimeoutError)` on timeout. `send` raises `ChannelClosedError` on a closed channel; iterating yields values until closed. Every op uses `notify_all` (O(waiters)) for correctness under contention. `ChannelClosedError` and `ChannelTimeoutError` are exported from `katharos.concurrency`.

### Operator summary

| Operator | Method | Meaning |
|----------|--------|---------|
| `\|` | `bind` | Monadic bind (`>>=`) in Haskell |
| `**` | `ap` | Applicative apply (`<*>`) in Haskell |
| `>>` | `then` | Sequence, `>>` in Haskell |
| `@` | `op` | Semigroup combine `<>` in Haskell|

### Test layout

Tests mirror `src/` under `tests/types/` and `tests/functools/` etc. Coverage is measured on the `katharos` package. Property-based tests use Hypothesis; shared algebra-law checkers (functor/applicative/monad/monoid laws) are factored out for reuse across types.

### Docstring conventions

Docstrings are Google-style, rendered by Sphinx (`sphinx.ext.napoleon`).

- **Do not put types in `Returns:` (or `Args:`) entries.** The code is fully annotated and `autodoc_typehints = "description"` pulls types from the signatures, so a docstring type is redundant and can silently drift. Write `Returns:` as a plain description (`A new Result containing the mapped value.`), not `Result[E, B]: ...`.
- Use Sphinx cross-reference roles for code references: `:meth:`, `:class:`, etc.
- `Examples:` blocks are runnable doctests — they must pass (`uv run python -m doctest <file>`), and exception output must match the real message (e.g. `'float division by zero'`).
