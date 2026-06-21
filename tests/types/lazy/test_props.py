"""Property-based tests for :class:`Lazy`.

These tests use Hypothesis to assert the algebraic laws and structural
invariants of :class:`Lazy` hold across a wide range of generated inputs,
complementing the worked-example tests in ``test_lazy.py``.

Note on equality: :class:`Lazy` has no value-based ``__eq__`` (two Lazies
compare by identity), so the algebraic laws cannot be checked on the Lazy
objects directly. Instead every law compares the *resolved* values of the
two sides. The strategies below therefore generate zero-argument *thunks*
(``() -> Lazy[int]``) rather than shared Lazy instances, so each side of a
law builds a fresh computation chain that is safe to resolve independently.
"""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from katharos.functools import F
from katharos.types.lazy import Lazy


def add_one(x: int) -> int:
    return x + 1


def double(x: int) -> int:
    return x * 2


def negate(x: int) -> int:
    return -x


def to_lazy_plus_one(x: int) -> Lazy[int]:
    return Lazy(fetcher=lambda: x + 1)


def to_lazy_double(x: int) -> Lazy[int]:
    return Lazy.pure(x * 2)


def to_lazy_square(x: int) -> Lazy[int]:
    return Lazy(fetcher=lambda: x * x)


# Strategies --------------------------------------------------------------

# Zero-argument thunks that each build a fresh Lazy[int]. Using thunks (not
# shared Lazy instances) keeps every law's two sides independent, since a
# resolved Lazy memoizes and cannot be re-driven from scratch.
lazy_thunks = st.integers().map(lambda n: lambda: Lazy(fetcher=lambda: n))
# Pure unary functions int -> int, sampled from a fixed pool.
funcs = st.sampled_from([add_one, double, negate, lambda x: x, lambda x: x * x])
# Kleisli arrows int -> Lazy[int], sampled from a fixed pool.
kleislis = st.sampled_from([to_lazy_plus_one, to_lazy_double, to_lazy_square])
# Thunks building a fresh Lazy[Callable] wrapping a sampled function.
lazy_func_thunks = funcs.map(lambda f: lambda: Lazy(fetcher=lambda: f))


class TestFunctorLaws:
    @given(lazy_thunks)
    def test_identity(self, mk):
        assert mk().fmap(F.id).resolve() == mk().resolve()

    @given(lazy_thunks, funcs, funcs)
    def test_composition(self, mk, f, g):
        left = mk().fmap(lambda x: g(f(x))).resolve()
        right = mk().fmap(f).fmap(g).resolve()
        assert left == right


class TestApplicativeLaws:
    @given(lazy_thunks)
    def test_identity(self, mk):
        assert mk().ap(Lazy.pure(F.id)).resolve() == mk().resolve()

    @given(st.integers(), funcs)
    def test_homomorphism(self, x: int, f):
        left = Lazy.pure(x).ap(Lazy.pure(f)).resolve()
        right = Lazy.pure(f(x)).resolve()
        assert left == right

    @given(st.integers(), lazy_func_thunks)
    def test_interchange(self, y: int, mku):
        left = Lazy.pure(y).ap(mku()).resolve()
        right = mku().ap(Lazy.pure(lambda g: g(y))).resolve()
        assert left == right

    @given(lazy_func_thunks, lazy_func_thunks, lazy_thunks)
    def test_composition(self, mku, mkv, mkw):
        left = mkw().ap(mkv()).ap(mku()).resolve()
        right = mkw().ap(mkv().ap(mku().ap(Lazy.pure(F.compose)))).resolve()
        assert left == right


class TestMonadLaws:
    @given(st.integers(), kleislis)
    def test_left_identity(self, a: int, f):
        assert Lazy.pure(a).bind(f).resolve() == f(a).resolve()

    @given(lazy_thunks)
    def test_right_identity(self, mk):
        assert mk().bind(Lazy.pure).resolve() == mk().resolve()

    @given(lazy_thunks, kleislis, kleislis)
    def test_associativity(self, mk, f, g):
        left = mk().bind(f).bind(g).resolve()
        right = mk().bind(lambda x: f(x).bind(g)).resolve()
        assert left == right


class TestLaziness:
    @given(st.integers())
    def test_construction_does_not_run_fetcher(self, x: int):
        calls = []

        def fetcher() -> int:
            calls.append(None)
            return x

        lazy = Lazy(fetcher=fetcher)
        assert calls == []  # not run until resolved
        lazy.resolve()
        assert len(calls) == 1

    @given(lazy_thunks, funcs, kleislis)
    def test_composition_does_not_run_fetcher(self, mk, f, k):
        calls = []
        base = Lazy(fetcher=lambda: (calls.append(None), 0)[1])
        # Building a whole chain triggers no evaluation.
        _ = base.fmap(f).bind(k).ap(mk().fmap(lambda _: f))
        assert calls == []


class TestMemoization:
    @given(st.integers(), st.integers(min_value=1, max_value=5))
    def test_fetcher_runs_at_most_once(self, x: int, n: int):
        calls = []

        def fetcher() -> int:
            calls.append(None)
            return x

        lazy = Lazy(fetcher=fetcher)
        results = [lazy.resolve() for _ in range(n)]
        assert results == [x] * n
        assert len(calls) == 1

    @given(st.integers())
    def test_resolve_is_idempotent(self, x: int):
        lazy = Lazy(fetcher=lambda: x)
        assert lazy.resolve() == lazy.resolve()

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
                lazy.resolve()
            assert exc_info.value is err
        # Failure is evaluated at most once, just like success.
        assert len(calls) == 1


class TestOperatorEquivalence:
    @given(lazy_thunks, kleislis)
    def test_pipe_equals_bind(self, mk, f):
        assert (mk() | f).resolve() == mk().bind(f).resolve()

    @given(lazy_thunks, lazy_func_thunks)
    def test_pow_equals_ap(self, mk, mkf):
        assert (mk() ** mkf()).resolve() == mk().ap(mkf()).resolve()

    @given(lazy_thunks, lazy_thunks)
    def test_rshift_discards_left(self, mk, mkother):
        # `a >> b` sequences and yields b's value, ignoring a's.
        assert (mk() >> mkother()).resolve() == mkother().resolve()


class TestPureAndRet:
    @given(st.integers())
    def test_pure_resolves_to_value(self, x: int):
        assert Lazy.pure(x).resolve() == x

    @given(st.integers())
    def test_ret_equals_pure(self, x: int):
        assert Lazy.ret(x).resolve() == Lazy.pure(x).resolve()
