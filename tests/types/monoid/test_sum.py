import decimal

import pytest

from katharos.types.monoid import Sum


class TestSumInt:
    def test_identity_returns_zero(self):
        identity = Sum[int].identity()
        assert identity._value == 0

    def test_op_adds_values(self):
        a = Sum(5)
        b = Sum(3)
        result = a.op(b)
        assert result._value == 8

    def test_left_identity_law(self):
        identity = Sum[int].identity()
        a = Sum(42)
        result = identity.op(a)
        assert result._value == a._value

    def test_right_identity_law(self):
        identity = Sum[int].identity()
        a = Sum(42)
        result = a.op(identity)
        assert result._value == a._value

    def test_associativity_law(self):
        a = Sum(5)
        b = Sum(10)
        c = Sum(15)
        left_assoc = a.op(b).op(c)
        right_assoc = a.op(b.op(c))
        assert left_assoc._value == right_assoc._value

    def test_associativity_law_with_negatives(self):
        a = Sum(-5)
        b = Sum(10)
        c = Sum(-3)
        left_assoc = a.op(b).op(c)
        right_assoc = a.op(b.op(c))
        assert left_assoc._value == right_assoc._value

    def test_repr(self):
        a = Sum(42)
        assert repr(a) == "Sum(42)"


class TestSumFloat:
    def test_identity_returns_zero(self):
        identity = Sum[float].identity()
        assert identity._value == 0.0

    def test_op_adds_values(self):
        a = Sum(5.5)
        b = Sum(3.2)
        result = a.op(b)
        assert result._value == pytest.approx(8.7)

    def test_left_identity_law(self):
        identity = Sum[float].identity()
        a = Sum(42.5)
        result = identity.op(a)
        assert result._value == pytest.approx(a._value)

    def test_right_identity_law(self):
        identity = Sum[float].identity()
        a = Sum(42.5)
        result = a.op(identity)
        assert result._value == pytest.approx(a._value)

    def test_associativity_law(self):
        a = Sum(5.1)
        b = Sum(10.2)
        c = Sum(15.3)
        left_assoc = a.op(b).op(c)
        right_assoc = a.op(b.op(c))
        assert left_assoc._value == pytest.approx(right_assoc._value)

    def test_repr(self):
        a = Sum(42.5)
        assert repr(a) == "Sum(42.5)"


class TestSumComplex:
    def test_identity_returns_zero(self):
        identity = Sum[complex].identity()
        assert identity._value == 0j

    def test_op_adds_values(self):
        a = Sum(3 + 4j)
        b = Sum(1 + 2j)
        result = a.op(b)
        assert result._value == 4 + 6j

    def test_left_identity_law(self):
        identity = Sum[complex].identity()
        a = Sum(3 + 4j)
        result = identity.op(a)
        assert result._value == a._value

    def test_right_identity_law(self):
        identity = Sum[complex].identity()
        a = Sum(3 + 4j)
        result = a.op(identity)
        assert result._value == a._value

    def test_associativity_law(self):
        a = Sum(1 + 2j)
        b = Sum(3 + 4j)
        c = Sum(5 + 6j)
        left_assoc = a.op(b).op(c)
        right_assoc = a.op(b.op(c))
        assert left_assoc._value == right_assoc._value

    def test_repr(self):
        a = Sum(3 + 4j)
        assert repr(a) == "Sum((3+4j))"


class TestSumDecimal:
    def test_identity_returns_zero(self):
        identity = Sum[decimal.Decimal].identity()
        assert identity._value == decimal.Decimal("0")

    def test_op_adds_values(self):
        a = Sum(decimal.Decimal("5.5"))
        b = Sum(decimal.Decimal("3.2"))
        result = a.op(b)
        assert result._value == decimal.Decimal("8.7")

    def test_left_identity_law(self):
        identity = Sum[decimal.Decimal].identity()
        a = Sum(decimal.Decimal("42.5"))
        result = identity.op(a)
        assert result._value == a._value

    def test_right_identity_law(self):
        identity = Sum[decimal.Decimal].identity()
        a = Sum(decimal.Decimal("42.5"))
        result = a.op(identity)
        assert result._value == a._value

    def test_associativity_law(self):
        a = Sum(decimal.Decimal("5.1"))
        b = Sum(decimal.Decimal("10.2"))
        c = Sum(decimal.Decimal("15.3"))
        left_assoc = a.op(b).op(c)
        right_assoc = a.op(b.op(c))
        assert left_assoc._value == right_assoc._value

    def test_associativity_law_with_precision(self):
        a = Sum(decimal.Decimal("0.1"))
        b = Sum(decimal.Decimal("0.2"))
        c = Sum(decimal.Decimal("0.3"))
        left_assoc = a.op(b).op(c)
        right_assoc = a.op(b.op(c))
        assert left_assoc._value == right_assoc._value

    def test_repr(self):
        a = Sum(decimal.Decimal("42.5"))
        assert repr(a) == "Sum(Decimal('42.5'))"


class TestSumEdgeCases:
    def test_identity_without_type_raises_error(self):
        with pytest.raises(AttributeError):
            Sum.identity()

    def test_multiple_operations_preserve_associativity(self):
        a = Sum(1)
        b = Sum(2)
        c = Sum(3)
        d = Sum(4)
        result1 = a.op(b).op(c).op(d)
        result2 = a.op(b.op(c.op(d)))
        result3 = a.op(b.op(c)).op(d)
        assert result1._value == result2._value == result3._value == 10

    def test_zero_values(self):
        a = Sum(0)
        b = Sum(0)
        result = a.op(b)
        assert result._value == 0

    def test_large_values(self):
        a = Sum(10**100)
        b = Sum(10**100)
        result = a.op(b)
        assert result._value == 2 * (10**100)
