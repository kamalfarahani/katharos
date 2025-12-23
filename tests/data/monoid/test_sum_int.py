from katharos.data.monoid.sum_int import SumInt


class TestSumIntAssociativity:
    def test_associativity_positive_numbers(self):
        a = SumInt(2)
        b = SumInt(3)
        c = SumInt(5)

        left = (a @ b) @ c
        right = a @ (b @ c)

        assert left.value == right.value
        assert left.value == 10

    def test_associativity_with_negative_numbers(self):
        a = SumInt(-2)
        b = SumInt(4)
        c = SumInt(-3)

        left = (a @ b) @ c
        right = a @ (b @ c)

        assert left.value == right.value
        assert left.value == -1

    def test_associativity_with_zero(self):
        a = SumInt(5)
        b = SumInt(0)
        c = SumInt(7)

        left = (a @ b) @ c
        right = a @ (b @ c)

        assert left.value == right.value
        assert left.value == 12

    def test_associativity_all_negative(self):
        a = SumInt(-7)
        b = SumInt(-1)
        c = SumInt(-11)

        left = (a @ b) @ c
        right = a @ (b @ c)

        assert left.value == right.value
        assert left.value == -19

    def test_associativity_large_numbers(self):
        a = SumInt(1000)
        b = SumInt(2000)
        c = SumInt(3000)

        left = (a @ b) @ c
        right = a @ (b @ c)

        assert left.value == right.value
        assert left.value == 6000


class TestSumIntIdentity:
    def test_left_identity_positive(self):
        identity = SumInt.identity()
        value = SumInt(42)

        result = identity @ value

        assert result.value == value.value
        assert result.value == 42

    def test_right_identity_positive(self):
        value = SumInt(42)
        identity = SumInt.identity()

        result = value @ identity

        assert result.value == value.value
        assert result.value == 42

    def test_left_identity_negative(self):
        identity = SumInt.identity()
        value = SumInt(-15)

        result = identity @ value

        assert result.value == value.value
        assert result.value == -15

    def test_right_identity_negative(self):
        value = SumInt(-15)
        identity = SumInt.identity()

        result = value @ identity

        assert result.value == value.value
        assert result.value == -15

    def test_left_identity_zero(self):
        identity = SumInt.identity()
        value = SumInt(0)

        result = identity @ value

        assert result.value == value.value
        assert result.value == 0

    def test_right_identity_zero(self):
        value = SumInt(0)
        identity = SumInt.identity()

        result = value @ identity

        assert result.value == value.value
        assert result.value == 0

    def test_identity_value_is_zero(self):
        identity = SumInt.identity()

        assert identity.value == 0

    def test_identity_with_large_number(self):
        identity = SumInt.identity()
        value = SumInt(999999)

        left_result = identity @ value
        right_result = value @ identity

        assert left_result.value == value.value
        assert right_result.value == value.value
        assert left_result.value == 999999


class TestSumIntBasicOperations:
    def test_addition_positive_numbers(self):
        a = SumInt(6)
        b = SumInt(7)

        result = a @ b

        assert result.value == 13

    def test_addition_negative_numbers(self):
        a = SumInt(-4)
        b = SumInt(-5)

        result = a @ b

        assert result.value == -9

    def test_addition_mixed_signs(self):
        a = SumInt(8)
        b = SumInt(-3)

        result = a @ b

        assert result.value == 5

    def test_addition_with_zero(self):
        a = SumInt(100)
        b = SumInt(0)

        result = a @ b

        assert result.value == 100

    def test_repr(self):
        value = SumInt(42)

        assert repr(value) == "SumInt(42)"
        assert str(value) == "SumInt(42)"
