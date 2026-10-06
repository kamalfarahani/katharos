import decimal

import pytest

from katharos.types.monoid import Product, Sum


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


class TestSumEquality:
    @pytest.mark.parametrize("value", [2, 2.5, 2 + 3j, decimal.Decimal("2.5")])
    def test_equal_wrapped_values(self, value):
        assert Sum(value) == Sum(value)

    def test_different_wrapped_values(self):
        assert Sum(2) != Sum(3)

    def test_separately_specialized_instances_compare_by_value(self):
        assert Sum[int](2) == Sum[int](2)
        assert Sum[int](2) == Sum(2)
        assert Sum[int](2) == Sum[float](2.0)

    @pytest.mark.parametrize("other", [2, None, object(), Product(2)])
    def test_unrelated_objects_are_not_equal(self, other):
        assert Sum(2) != other

    def test_unrelated_object_can_handle_reflected_comparison(self):
        class MatchesSum:
            def __eq__(self, other: object) -> bool:
                return isinstance(other, Sum) and other._value == 2

        assert Sum(2) == MatchesSum()


class TestSumHash:
    def test_equal_numeric_sums_deduplicate_in_set(self):
        sums = {
            Sum[int](2),
            Sum[int](2),
            Sum[float](2.0),
            Sum[complex](2 + 0j),
            Sum[decimal.Decimal](decimal.Decimal(2)),
        }
        assert len(sums) == 1

    def test_equal_sum_can_look_up_dictionary_entry(self):
        sums = {Sum[int](2): "two", Sum[int](3): "three"}
        assert sums[Sum[float](2.0)] == "two"
        assert sums[Sum(3)] == "three"
