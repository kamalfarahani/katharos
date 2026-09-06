"""Property-based tests for :class:`Lazy`.

These tests use Hypothesis to assert the algebraic laws and structural
invariants of :class:`Lazy` hold across a wide range of generated inputs,
complementing the worked-example tests in ``test_lazy.py``.

Note on equality: :class:`Lazy` has no value-based ``__eq__`` (two Lazies
compare by identity), so the algebraic laws are checked through a custom
comparator that forces both sides (``lambda a, b: a.force() == b.force()``).
Because :meth:`Lazy.force` memoizes, forcing the same Lazy more than once is
idempotent, so a single Lazy instance can safely back both sides of a law.
"""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from katharos.types.lazy import Lazy
from tests.law_helpers import (
    check_applicative_laws,
    check_functor_laws,
    check_monad_laws,
)
from tests.law_helpers import unary_int_funcs as funcs


def to_lazy_plus_one(x: int) -> Lazy[int]:
    return Lazy(fetcher=lambda: x + 1)


def to_lazy_double(x: int) -> Lazy[int]:
    return Lazy.pure(x * 2)


def to_lazy_square(x: int) -> Lazy[int]:
    return Lazy(fetcher=lambda: x * x)


# Comparator that drives both sides to a concrete value.
def forces_equal(a: Lazy, b: Lazy) -> bool:
    return a.force() == b.force()


# Strategies --------------------------------------------------------------

# Lazy[int] values, each wrapping a fresh fetcher.
lazies = st.integers().map(lambda n: Lazy(fetcher=lambda: n))
# Kleisli arrows int -> Lazy[int], sampled from a fixed pool.
kleislis = st.sampled_from([to_lazy_plus_one, to_lazy_double, to_lazy_square])
# Lazy[Callable] values wrapping a sampled function.
lazy_funcs = funcs.map(lambda f: Lazy(fetcher=lambda: f))


def test_functor_laws():
    check_functor_laws(lazies, eq=forces_equal)


def test_applicative_laws():
    check_applicative_laws(lazies, lazy_funcs, Lazy.pure, eq=forces_equal)


def test_monad_laws():
    check_monad_laws(lazies, kleislis, Lazy.pure, eq=forces_equal)


class TestLaziness:
    @given(st.integers())
    def test_construction_does_not_run_fetcher(self, x: int):
        calls = []

        def fetcher() -> int:
            calls.append(None)
            return x

        lazy = Lazy(fetcher=fetcher)
        assert calls == []  # not run until forced
        lazy.force()
        assert len(calls) == 1

    @given(lazies, funcs, kleislis)
    def test_composition_does_not_run_fetcher(self, lazy, f, k):
        calls = []
        base = Lazy(fetcher=lambda: (calls.append(None), 0)[1])
        # Building a whole chain triggers no evaluation.
        _ = base.fmap(f).bind(k).ap(lazy.fmap(lambda _: f))
        assert calls == []


class TestMemoization:
    @given(st.integers(), st.integers(min_value=1, max_value=5))
    def test_fetcher_runs_at_most_once(self, x: int, n: int):
        calls = []

        def fetcher() -> int:
            calls.append(None)
            return x

        lazy = Lazy(fetcher=fetcher)
        results = [lazy.force() for _ in range(n)]
        assert results == [x] * n
        assert len(calls) == 1

    @given(st.integers())
    def test_force_is_idempotent(self, x: int):
        lazy = Lazy(fetcher=lambda: x)
        assert lazy.force() == lazy.force()

    @given(st.integers(min_value=1, max_value=5))
    def test_raised_exception_is_memoized_and_reraised(self, n: int):
        calls = []
        err = ValueError("boom")

        def fetcher() -> int:
            calls.append(None)
            raise err

        lazy = Lazy(fetcher=fetcher)
        for _ in range(n):
            with pytest.raises(ValueError) as exc_info:
                lazy.force()
            assert exc_info.value is err
        # Failure is evaluated at most once, just like success.
        assert len(calls) == 1


class TestOperatorEquivalence:
    @given(lazies, kleislis)
    def test_pipe_equals_bind(self, lazy, f):
        assert (lazy | f).force() == lazy.bind(f).force()

    @given(lazies, lazy_funcs)
    def test_pow_equals_ap(self, lazy, wf):
        assert (lazy**wf).force() == lazy.ap(wf).force()

    @given(lazies, lazies)
    def test_rshift_discards_left(self, lazy, other):
        # `a >> b` sequences and yields b's value, ignoring a's.
        assert (lazy >> other).force() == other.force()


class TestPureAndRet:
    @given(st.integers())
    def test_pure_forces_to_value(self, x: int):
        assert Lazy.pure(x).force() == x

    @given(st.integers())
    def test_ret_equals_pure(self, x: int):
        assert Lazy.ret(x).force() == Lazy.pure(x).force()
