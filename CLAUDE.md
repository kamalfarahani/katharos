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

Katharos is a functional programming library structured in three layers:

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
| `IO[A]` | Monad | lazy side-effect wrapper; call `.execute()` to run |
| `MonoidMaybe` | Monoid | Maybe with a monoid instance |
| `Sum`, `Product` | Monoid | numeric monoids |

`Maybe` and `Result` are `@final` — do not subclass. Use `is_just()`/`is_nothing()` and `is_success()`/`is_failure()` for state checks rather than type checks.

### Layer 3: Utilities

- **`src/katharos/functools/f.py`** — `F` static namespace: `compose`, `id`, `foldr`, `foldl`, `sigma` (fold a `NonEmptyList[Semigroup]`), `curry`
- **`src/katharos/syntax_sugar/do.py`** — `do` decorator for Haskell-style do-notation:
  ```python
  @do(Maybe)
  def computation() -> DoBlock[int]:
      x: int = yield Maybe.Just(3)   # analogous to x <- Just 3 in Haskell
      y: int = yield Maybe.Just(4)
      return x + y
  ```
  Each `yield` unwraps the monadic value (short-circuits on `Nothing`/`Failure`). The plain `return` is automatically lifted via `Maybe.ret()`.

### Operator summary

| Operator | Method | Meaning |
|----------|--------|---------|
| `\|` | `bind` | Monadic bind (`>>=`) in Haskell |
| `**` | `ap` | Applicative apply (`<*>`) in Haskell |
| `>>` | `then` | Sequence, `>>` in Haskell |
| `@` | `op` | Semigroup combine `<>` in Haskell|

### Test layout

Tests mirror `src/` under `tests/types/` and `tests/functools/` etc. Coverage is measured on the `katharos` package.
