"""Property-based tests for :class:`Result`.

These tests use Hypothesis to assert the algebraic laws and structural
invariants of :class:`Result` hold across a wide range of generated inputs,
complementing the worked-example tests in the other ``test_result_*`` modules.

Note on equality: a ``Failure`` compares by the *identity* of its wrapped
exception (exceptions use identity equality by default). The strategies below
therefore draw from a fixed pool of shared exception instances, and the Kleisli
arrows return shared exception objects, so repeated calls of the same function
produce equal Results and the law equalities are well-defined.
"""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from katharos.types import UnwrapError
from katharos.types.result import Result
from tests.law_helpers import (
    check_applicative_laws,
    check_functor_laws,
    check_monad_laws,
    unary_int_funcs as funcs,
)

# Shared exception instances used by the failing Kleisli arrows so that
# calling them twice yields identity-equal Failures.
_DIV_ERR = ZeroDivisionError("division by zero")
_NEG_ERR = ValueError("not positive")


def safe_reciprocal(x: int) -> Result[BaseException, float]:
    return Result.Failure(_DIV_ERR) if x == 0 else Result.Success(1 / x)


def only_positive(x: int) -> Result[BaseException, int]:
    return Result.Success(x) if x > 0 else Result.Failure(_NEG_ERR)


# Strategies --------------------------------------------------------------

# A fixed pool of shared exception instances (compared by identity).
errors = st.sampled_from([ValueError("a"), KeyError("b"), RuntimeError("c")])
# Result[BaseException, int] values: Success(n) or Failure(exc).
results = st.one_of(
    st.integers().map(Result.Success),
    errors.map(Result.Failure),
)
# Kleisli arrows int -> Result[_, int], sampled from a fixed pool.
kleislis = st.sampled_from(
    [safe_reciprocal, only_positive, lambda x: Result.Success(x + 1)]
)
# Result wrapping a sampled function, or a Failure.
result_funcs = st.one_of(
    funcs.map(Result.Success),
    errors.map(Result.Failure),
)


def test_functor_laws():
    check_functor_laws(results)


def test_applicative_laws():
    check_applicative_laws(results, result_funcs, Result.pure)


def test_monad_laws():
    check_monad_laws(results, kleislis, Result.pure)


class TestStructuralProperties:
    @given(st.integers())
    def test_success_roundtrips_value(self, x: int):
        r = Result.Success(x)
        assert r.is_success()
        assert not r.is_failure()
        assert r.value == x
        assert r.unwrap() == x

    @given(st.integers())
    def test_pure_equals_success(self, x: int):
        assert Result.pure(x) == Result.Success(x)

    @given(results, funcs)
    def test_fmap_preserves_state(self, r: Result, f):
        # fmap never changes Success/Failure-ness.
        assert r.fmap(f).is_success() == r.is_success()

    @given(results)
    def test_bind_to_failure_is_failure(self, r: Result):
        # A Success transitions to the injected Failure; a Failure
        # short-circuits and keeps its own error. Either way: a Failure.
        assert r.bind(lambda _: Result.Failure(_NEG_ERR)).is_failure()

    @given(kleislis)
    def test_failure_short_circuits_bind(self, f):
        original = Result.Failure(_DIV_ERR)
        # Binding from a Failure returns it unchanged.
        assert original.bind(f) == original

    @given(result_funcs)
    def test_failure_value_ap_is_failure(self, wf: Result):
        assert Result.Failure(_DIV_ERR).ap(wf).is_failure()


class TestCatch:
    @given(st.integers())
    def test_catch_wraps_outcome(self, x: int):
        @Result.catch(ZeroDivisionError)
        def reciprocal(n: int) -> float:
            return 1 / n

        out = reciprocal(x)
        if x == 0:
            assert out.is_failure()
            assert isinstance(out.error, ZeroDivisionError)
        else:
            assert out.is_success()
            assert out.value == 1 / x

    def test_catch_only_declared_exception(self):
        @Result.catch(ValueError)
        def boom() -> int:
            raise TypeError("nope")

        with pytest.raises(TypeError):
            boom()


class TestOperatorEquivalence:
    @given(results, kleislis)
    def test_pipe_equals_bind(self, r: Result, f):
        assert (r | f) == r.bind(f)

    @given(results, result_funcs)
    def test_pow_equals_ap(self, r: Result, wf: Result):
        assert (r**wf) == r.ap(wf)


class TestEqualityAndHash:
    @given(results)
    def test_reflexive(self, r: Result):
        assert r == r

    @given(st.integers(), st.integers())
    def test_success_equal_iff_same_value(self, a: int, b: int):
        assert (Result.Success(a) == Result.Success(b)) == (a == b)

    @given(results)
    def test_success_never_equals_failure(self, r: Result):
        other = Result.Failure(_DIV_ERR) if r.is_success() else Result.Success(0)
        assert r != other

    @given(results)
    def test_not_equal_to_non_result(self, r: Result):
        assert r != object()

    @given(results, results)
    def test_equal_implies_same_hash(self, r: Result, s: Result):
        if r == s:
            assert hash(r) == hash(s)


class TestAccessors:
    def test_value_on_failure_raises(self):
        with pytest.raises(UnwrapError, match="Cannot get the value of a Failure"):
            _ = Result.Failure(_DIV_ERR).value

    def test_unwrap_on_failure_raises(self):
        with pytest.raises(UnwrapError):
            Result.Failure(_DIV_ERR).unwrap()

    def test_error_on_success_raises(self):
        with pytest.raises(UnwrapError, match="Cannot get the error of a Success"):
            _ = Result.Success(1).error

    def test_failure_requires_exception(self):
        with pytest.raises(TypeError, match="non-exception"):
            Result.Failure(42)  # type: ignore[arg-type]
