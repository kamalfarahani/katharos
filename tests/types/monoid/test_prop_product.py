"""Property-based tests for :class:`Product`.

These tests use Hypothesis to assert the monoid laws of :class:`Product` hold
across a wide range of generated values, complementing the worked-example
tests in ``test_product.py``.

:class:`Product` is a :class:`~katharos.algebra.Monoid` under multiplication.
It has no value-based ``__eq__``, so results are compared through ``._value``.
Integer and ``Decimal`` arithmetic is exact (bounded magnitude keeps the
product of three inside the decimal context precision), so those laws use
``==``; ``float`` and ``complex`` use :func:`pytest.approx` to absorb rounding.
"""

import decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from katharos.types.monoid import Product
from tests.law_helpers import check_monoid_laws


# Comparators on the wrapped ``._value`` (Product has no value-based __eq__).
def exact_eq(a, b) -> bool:
    return a._value == b._value


def approx_eq(a, b) -> bool:
    return a._value == pytest.approx(b._value)


# Strategies --------------------------------------------------------------

ints = st.integers(min_value=-(10**6), max_value=10**6)
# Bounded so that products of three stay finite and precise.
floats = st.floats(
    allow_nan=False,
    allow_infinity=False,
    allow_subnormal=False,
    min_value=-100.0,
    max_value=100.0,
)
# Bounded so that the product of three stays inside the 28-digit context.
decimals = st.decimals(
    min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False, places=2
)
complexes = st.complex_numbers(allow_nan=False, allow_infinity=False, max_magnitude=100)


def test_int_monoid_laws():
    check_monoid_laws(ints.map(Product), lambda: Product[int].identity(), eq=exact_eq)


def test_float_monoid_laws():
    check_monoid_laws(
        floats.map(Product), lambda: Product[float].identity(), eq=approx_eq
    )


def test_complex_monoid_laws():
    check_monoid_laws(
        complexes.map(Product), lambda: Product[complex].identity(), eq=approx_eq
    )


def test_decimal_monoid_laws():
    check_monoid_laws(
        decimals.map(Product), lambda: Product[decimal.Decimal].identity(), eq=exact_eq
    )


@given(ints, ints)
def test_op_multiplies(a: int, b: int):
    assert Product(a).op(Product(b))._value == a * b


class TestProductStructural:
    @given(ints, ints)
    def test_matmul_equals_op(self, a: int, b: int):
        # `@` is the Semigroup operator for op.
        assert (Product(a) @ Product(b))._value == Product(a).op(Product(b))._value

    @given(ints)
    def test_identity_is_one(self, x: int):
        # Combining with identity on either side is a no-op.
        identity = Product[int].identity()
        assert identity._value == 1
        assert Product(x).op(identity)._value == identity.op(Product(x))._value == x

    @given(ints)
    def test_zero_annihilates(self, x: int):
        zero = Product(0)
        assert Product(x).op(zero)._value == zero.op(Product(x))._value == 0

    def test_identity_without_type_raises(self):
        with pytest.raises(AttributeError):
            Product.identity()
