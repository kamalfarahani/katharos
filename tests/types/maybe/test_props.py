"""Property-based tests for :class:`Maybe`.

These tests use Hypothesis to assert the algebraic laws and structural
invariants of :class:`Maybe` hold across a wide range of generated inputs,
complementing the worked-example tests in ``test_maybe.py``.
"""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from katharos.functools import F
from katharos.types.maybe import Maybe


def add_one(x: int) -> int:
    return x + 1


def double(x: int) -> int:
    return x * 2


def negate(x: int) -> int:
    return -x


def safe_reciprocal(x: int) -> Maybe[float]:
    return Maybe.Nothing() if x == 0 else Maybe.Just(1 / x)


def only_positive(x: int) -> Maybe[int]:
    return Maybe.Just(x) if x > 0 else Maybe.Nothing()


# Strategies --------------------------------------------------------------

# Maybe[int] values: Just(n) or Nothing()
maybes = st.one_of(
    st.integers().map(Maybe.Just),
    st.just(Maybe.Nothing()),
)
# Pure unary functions int -> int, sampled from a fixed pool.
funcs = st.sampled_from([add_one, double, negate, lambda x: x, lambda x: x * x])
# Kleisli arrows int -> Maybe[int], sampled from a fixed pool.
kleislis = st.sampled_from(
    [safe_reciprocal, only_positive, lambda x: Maybe.Just(x + 1)]
)
# Maybe[Callable] values wrapping a sampled function, or Nothing.
maybe_funcs = st.one_of(
    funcs.map(Maybe.Just),
    st.just(Maybe.Nothing()),
)


class TestFunctorLaws:
    @given(maybes)
    def test_identity(self, m: Maybe[int]):
        assert m.fmap(F.id) == m

    @given(maybes, funcs, funcs)
    def test_composition(self, m: Maybe[int], f, g):
        assert m.fmap(lambda x: g(f(x))) == m.fmap(f).fmap(g)


class TestApplicativeLaws:
    @given(maybes)
    def test_identity(self, v: Maybe[int]):
        assert v.ap(Maybe.pure(F.id)) == v

    @given(st.integers(), funcs)
    def test_homomorphism(self, x: int, f):
        assert Maybe.pure(x).ap(Maybe.pure(f)) == Maybe.pure(f(x))

    @given(st.integers(), maybe_funcs)
    def test_interchange(self, y: int, u: Maybe):
        left = Maybe.pure(y).ap(u)
        right = u.ap(Maybe.pure(lambda g: g(y)))
        assert left == right

    @given(maybe_funcs, maybe_funcs, maybes)
    def test_composition(self, u: Maybe, v: Maybe, w: Maybe[int]):
        left = w.ap(v).ap(u)
        right = w.ap(v.ap(u.ap(Maybe.pure(F.compose))))
        assert left == right


class TestMonadLaws:
    @given(st.integers(), kleislis)
    def test_left_identity(self, a: int, f):
        assert Maybe.pure(a).bind(f) == f(a)

    @given(maybes)
    def test_right_identity(self, m: Maybe[int]):
        assert m.bind(Maybe.pure) == m

    @given(maybes, kleislis, kleislis)
    def test_associativity(self, m: Maybe[int], f, g):
        left = m.bind(f).bind(g)
        right = m.bind(lambda x: f(x).bind(g))
        assert left == right


class TestStructuralProperties:
    @given(st.integers())
    def test_just_roundtrips_value(self, x: int):
        m = Maybe.Just(x)
        assert m.is_just()
        assert not m.is_nothing()
        assert m.unwrap() == x

    @given(st.integers())
    def test_pure_equals_just(self, x: int):
        assert Maybe.pure(x) == Maybe.Just(x)

    @given(maybes, funcs)
    def test_fmap_preserves_state(self, m: Maybe[int], f):
        # fmap never changes Just/Nothing-ness.
        assert m.fmap(f).is_just() == m.is_just()

    @given(maybes)
    def test_bind_to_nothing_is_nothing(self, m: Maybe[int]):
        assert m.bind(lambda _: Maybe.Nothing()).is_nothing()

    @given(kleislis)
    def test_nothing_short_circuits_bind(self, f):
        # Binding from Nothing always yields Nothing.
        assert Maybe.Nothing().bind(f).is_nothing()

    @given(maybe_funcs)
    def test_ap_nothing_value_is_nothing(self, wf: Maybe):
        assert Maybe.Nothing().ap(wf).is_nothing()


class TestOperatorEquivalence:
    @given(maybes, kleislis)
    def test_pipe_equals_bind(self, m: Maybe[int], f):
        assert (m | f) == m.bind(f)

    @given(maybes, maybe_funcs)
    def test_pow_equals_ap(self, m: Maybe[int], wf: Maybe):
        assert (m**wf) == m.ap(wf)


class TestEqualityAndHash:
    @given(maybes)
    def test_reflexive(self, m: Maybe[int]):
        assert m == m

    @given(st.integers(), st.integers())
    def test_equal_iff_same_state_and_value(self, a: int, b: int):
        assert (Maybe.Just(a) == Maybe.Just(b)) == (a == b)

    @given(maybes)
    def test_not_equal_to_non_maybe(self, m: Maybe[int]):
        assert m != object()

    @given(maybes, maybes)
    def test_equal_implies_same_hash(self, m: Maybe[int], n: Maybe[int]):
        if m == n:
            assert hash(m) == hash(n)


class TestUnwrap:
    def test_unwrap_nothing_raises(self):
        with pytest.raises(ValueError, match="Cannot unwrap a Nothing"):
            Maybe.Nothing().unwrap()
