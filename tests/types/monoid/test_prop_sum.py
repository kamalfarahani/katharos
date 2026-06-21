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
from tests.law_helpers import check_monoid_laws


# Comparators on the wrapped ``._value`` (Sum has no value-based __eq__).
def exact_eq(a, b) -> bool:
    return a._value == b._value


def approx_eq(a, b) -> bool:
    return a._value == pytest.approx(b._value)


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


def test_int_monoid_laws():
    check_monoid_laws(ints.map(Sum), lambda: Sum[int].identity(), eq=exact_eq)


def test_float_monoid_laws():
    check_monoid_laws(floats.map(Sum), lambda: Sum[float].identity(), eq=approx_eq)


def test_complex_monoid_laws():
    check_monoid_laws(complexes.map(Sum), lambda: Sum[complex].identity(), eq=approx_eq)


def test_decimal_monoid_laws():
    check_monoid_laws(
        decimals.map(Sum), lambda: Sum[decimal.Decimal].identity(), eq=exact_eq
    )


@given(ints, ints)
def test_op_adds(a: int, b: int):
    assert Sum(a).op(Sum(b))._value == a + b


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
