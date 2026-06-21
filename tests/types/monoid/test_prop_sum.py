"""Property-based tests for :class:`Sum`.

These tests use Hypothesis to assert the monoid laws of :class:`Sum` hold
across a wide range of generated values, complementing the worked-example
tests in ``test_sum.py``.

:class:`Sum` is a :class:`~katharos.algebra.Monoid` under addition. It has no
value-based ``__eq__``, so results are compared through ``._value``. Integer
and ``Decimal`` arithmetic is exact (bounded magnitude keeps the latter inside
the decimal context precision), so those laws use ``==``; ``float`` and
``complex`` use :func:`pytest.approx` to absorb rounding.
"""

import decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from katharos.types.monoid import Sum

# Strategies --------------------------------------------------------------

ints = st.integers(min_value=-(10**9), max_value=10**9)
floats = st.floats(
    allow_nan=False,
    allow_infinity=False,
    allow_subnormal=False,
    min_value=-1e3,
    max_value=1e3,
)
# Bounded so that sums of three stay well inside the default 28-digit context.
decimals = st.decimals(
    min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False, places=2
)
complexes = st.complex_numbers(allow_nan=False, allow_infinity=False, max_magnitude=1e3)


class TestSumIntLaws:
    @given(ints)
    def test_left_identity(self, x: int):
        assert Sum[int].identity().op(Sum(x))._value == x

    @given(ints)
    def test_right_identity(self, x: int):
        assert Sum(x).op(Sum[int].identity())._value == x

    @given(ints, ints, ints)
    def test_associativity(self, a: int, b: int, c: int):
        left = Sum(a).op(Sum(b)).op(Sum(c))
        right = Sum(a).op(Sum(b).op(Sum(c)))
        assert left._value == right._value

    @given(ints, ints)
    def test_op_adds(self, a: int, b: int):
        assert Sum(a).op(Sum(b))._value == a + b


class TestSumFloatLaws:
    @given(floats)
    def test_left_identity(self, x: float):
        assert Sum[float].identity().op(Sum(x))._value == x

    @given(floats)
    def test_right_identity(self, x: float):
        assert Sum(x).op(Sum[float].identity())._value == x

    @given(floats, floats, floats)
    def test_associativity(self, a: float, b: float, c: float):
        left = Sum(a).op(Sum(b)).op(Sum(c))
        right = Sum(a).op(Sum(b).op(Sum(c)))
        assert left._value == pytest.approx(right._value)


class TestSumComplexLaws:
    @given(complexes)
    def test_left_identity(self, x: complex):
        assert Sum[complex].identity().op(Sum(x))._value == x

    @given(complexes)
    def test_right_identity(self, x: complex):
        assert Sum(x).op(Sum[complex].identity())._value == x

    @given(complexes, complexes, complexes)
    def test_associativity(self, a: complex, b: complex, c: complex):
        left = Sum(a).op(Sum(b)).op(Sum(c))
        right = Sum(a).op(Sum(b).op(Sum(c)))
        assert left._value == pytest.approx(right._value)


class TestSumDecimalLaws:
    @given(decimals)
    def test_left_identity(self, x: decimal.Decimal):
        assert Sum[decimal.Decimal].identity().op(Sum(x))._value == x

    @given(decimals)
    def test_right_identity(self, x: decimal.Decimal):
        assert Sum(x).op(Sum[decimal.Decimal].identity())._value == x

    @given(decimals, decimals, decimals)
    def test_associativity(
        self, a: decimal.Decimal, b: decimal.Decimal, c: decimal.Decimal
    ):
        left = Sum(a).op(Sum(b)).op(Sum(c))
        right = Sum(a).op(Sum(b).op(Sum(c)))
        assert left._value == right._value


class TestSumStructural:
    @given(ints, ints)
    def test_matmul_equals_op(self, a: int, b: int):
        # `@` is the Semigroup operator for op.
        assert (Sum(a) @ Sum(b))._value == Sum(a).op(Sum(b))._value

    @given(ints)
    def test_identity_is_zero(self, x: int):
        # Combining with identity on either side is a no-op.
        identity = Sum[int].identity()
        assert identity._value == 0
        assert Sum(x).op(identity)._value == identity.op(Sum(x))._value == x

    def test_identity_without_type_raises(self):
        with pytest.raises(AttributeError):
            Sum.identity()
