import decimal

import pytest

from katharos.types.monoid import Product


class TestProductInt:
    def test_identity_returns_one(self):
        identity = Product[int].identity()
        assert identity._value == 1

    def test_op_multiplies_values(self):
        a = Product(5)
        b = Product(3)
        result = a.op(b)
        assert result._value == 15

    def test_left_identity_law(self):
        identity = Product[int].identity()
        a = Product(42)
        result = identity.op(a)
        assert result._value == a._value

    def test_right_identity_law(self):
        identity = Product[int].identity()
        a = Product(42)
        result = a.op(identity)
        assert result._value == a._value

    def test_associativity_law(self):
        a = Product(5)
        b = Product(10)
        c = Product(15)
        left_assoc = a.op(b).op(c)
        right_assoc = a.op(b.op(c))
        assert left_assoc._value == right_assoc._value

    def test_associativity_law_with_negatives(self):
        a = Product(-5)
        b = Product(10)
        c = Product(-3)
        left_assoc = a.op(b).op(c)
        right_assoc = a.op(b.op(c))
        assert left_assoc._value == right_assoc._value

    def test_repr(self):
        a = Product(42)
        assert repr(a) == "Product(42)"


class TestProductFloat:
    def test_identity_returns_one(self):
        identity = Product[float].identity()
        assert identity._value == 1.0

    def test_op_multiplies_values(self):
        a = Product(5.5)
        b = Product(2.0)
        result = a.op(b)
        assert result._value == pytest.approx(11.0)

    def test_left_identity_law(self):
        identity = Product[float].identity()
        a = Product(42.5)
        result = identity.op(a)
        assert result._value == pytest.approx(a._value)

    def test_right_identity_law(self):
        identity = Product[float].identity()
        a = Product(42.5)
        result = a.op(identity)
        assert result._value == pytest.approx(a._value)

    def test_associativity_law(self):
        a = Product(2.0)
        b = Product(3.0)
        c = Product(4.0)
        left_assoc = a.op(b).op(c)
        right_assoc = a.op(b.op(c))
        assert left_assoc._value == pytest.approx(right_assoc._value)

    def test_repr(self):
        a = Product(42.5)
        assert repr(a) == "Product(42.5)"


class TestProductComplex:
    def test_identity_returns_one(self):
        identity = Product[complex].identity()
        assert identity._value == 1 + 0j

    def test_op_multiplies_values(self):
        a = Product(3 + 4j)
        b = Product(1 + 2j)
        result = a.op(b)
        assert result._value == (3 + 4j) * (1 + 2j)

    def test_left_identity_law(self):
        identity = Product[complex].identity()
        a = Product(3 + 4j)
        result = identity.op(a)
        assert result._value == a._value

    def test_right_identity_law(self):
        identity = Product[complex].identity()
        a = Product(3 + 4j)
        result = a.op(identity)
        assert result._value == a._value

    def test_associativity_law(self):
        a = Product(1 + 2j)
        b = Product(3 + 4j)
        c = Product(5 + 6j)
        left_assoc = a.op(b).op(c)
        right_assoc = a.op(b.op(c))
        assert left_assoc._value == right_assoc._value

    def test_repr(self):
        a = Product(3 + 4j)
        assert repr(a) == "Product((3+4j))"


class TestProductDecimal:
    def test_identity_returns_one(self):
        identity = Product[decimal.Decimal].identity()
        assert identity._value == decimal.Decimal("1")

    def test_op_multiplies_values(self):
        a = Product(decimal.Decimal("5.5"))
        b = Product(decimal.Decimal("2.0"))
        result = a.op(b)
        assert result._value == decimal.Decimal("11.0")

    def test_left_identity_law(self):
        identity = Product[decimal.Decimal].identity()
        a = Product(decimal.Decimal("42.5"))
        result = identity.op(a)
        assert result._value == a._value

    def test_right_identity_law(self):
        identity = Product[decimal.Decimal].identity()
        a = Product(decimal.Decimal("42.5"))
        result = a.op(identity)
        assert result._value == a._value

    def test_associativity_law(self):
        a = Product(decimal.Decimal("2.0"))
        b = Product(decimal.Decimal("3.0"))
        c = Product(decimal.Decimal("4.0"))
        left_assoc = a.op(b).op(c)
        right_assoc = a.op(b.op(c))
        assert left_assoc._value == right_assoc._value

    def test_associativity_law_with_precision(self):
        a = Product(decimal.Decimal("1.1"))
        b = Product(decimal.Decimal("2.2"))
        c = Product(decimal.Decimal("3.3"))
        left_assoc = a.op(b).op(c)
        right_assoc = a.op(b.op(c))
        assert left_assoc._value == right_assoc._value

    def test_repr(self):
        a = Product(decimal.Decimal("42.5"))
        assert repr(a) == "Product(Decimal('42.5'))"


class TestProductEdgeCases:
    def test_identity_without_type_raises_error(self):
        with pytest.raises(AttributeError):
            Product.identity()

    def test_multiple_operations_preserve_associativity(self):
        a = Product(2)
        b = Product(3)
        c = Product(4)
        d = Product(5)
        result1 = a.op(b).op(c).op(d)
        result2 = a.op(b.op(c.op(d)))
        result3 = a.op(b.op(c)).op(d)
        assert result1._value == result2._value == result3._value == 120

    def test_zero_annihilates(self):
        a = Product(0)
        b = Product(42)
        result = a.op(b)
        assert result._value == 0

    def test_one_values(self):
        a = Product(1)
        b = Product(1)
        result = a.op(b)
        assert result._value == 1

    def test_large_values(self):
        a = Product(10**50)
        b = Product(10**50)
        result = a.op(b)
        assert result._value == 10**100
