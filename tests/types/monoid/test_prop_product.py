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


class TestProductIntLaws:
    @given(ints)
    def test_left_identity(self, x: int):
        assert Product[int].identity().op(Product(x))._value == x

    @given(ints)
    def test_right_identity(self, x: int):
        assert Product(x).op(Product[int].identity())._value == x

    @given(ints, ints, ints)
    def test_associativity(self, a: int, b: int, c: int):
        left = Product(a).op(Product(b)).op(Product(c))
        right = Product(a).op(Product(b).op(Product(c)))
        assert left._value == right._value

    @given(ints, ints)
    def test_op_multiplies(self, a: int, b: int):
        assert Product(a).op(Product(b))._value == a * b


class TestProductFloatLaws:
    @given(floats)
    def test_left_identity(self, x: float):
        assert Product[float].identity().op(Product(x))._value == x

    @given(floats)
    def test_right_identity(self, x: float):
        assert Product(x).op(Product[float].identity())._value == x

    @given(floats, floats, floats)
    def test_associativity(self, a: float, b: float, c: float):
        left = Product(a).op(Product(b)).op(Product(c))
        right = Product(a).op(Product(b).op(Product(c)))
        assert left._value == pytest.approx(right._value)


class TestProductComplexLaws:
    @given(complexes)
    def test_left_identity(self, x: complex):
        assert Product[complex].identity().op(Product(x))._value == x

    @given(complexes)
    def test_right_identity(self, x: complex):
        assert Product(x).op(Product[complex].identity())._value == x

    @given(complexes, complexes, complexes)
    def test_associativity(self, a: complex, b: complex, c: complex):
        left = Product(a).op(Product(b)).op(Product(c))
        right = Product(a).op(Product(b).op(Product(c)))
        assert left._value == pytest.approx(right._value)


class TestProductDecimalLaws:
    @given(decimals)
    def test_left_identity(self, x: decimal.Decimal):
        assert Product[decimal.Decimal].identity().op(Product(x))._value == x

    @given(decimals)
    def test_right_identity(self, x: decimal.Decimal):
        assert Product(x).op(Product[decimal.Decimal].identity())._value == x

    @given(decimals, decimals, decimals)
    def test_associativity(
        self, a: decimal.Decimal, b: decimal.Decimal, c: decimal.Decimal
    ):
        left = Product(a).op(Product(b)).op(Product(c))
        right = Product(a).op(Product(b).op(Product(c)))
        assert left._value == right._value


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
