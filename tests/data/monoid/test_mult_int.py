from katharos.data.monoid.mult_int import MultInt


class TestMultIntAssociativity:
    def test_associativity_positive_numbers(self):
        a = MultInt(2)
        b = MultInt(3)
        c = MultInt(5)

        left = (a @ b) @ c
        right = a @ (b @ c)

        assert left.value == right.value
        assert left.value == 30

    def test_associativity_with_negative_numbers(self):
        a = MultInt(-2)
        b = MultInt(4)
        c = MultInt(-3)

        left = (a @ b) @ c
        right = a @ (b @ c)

        assert left.value == right.value
        assert left.value == 24

    def test_associativity_with_zero(self):
        a = MultInt(5)
        b = MultInt(0)
        c = MultInt(7)

        left = (a @ b) @ c
        right = a @ (b @ c)

        assert left.value == right.value
        assert left.value == 0

    def test_associativity_with_one(self):
        a = MultInt(7)
        b = MultInt(1)
        c = MultInt(11)

        left = (a @ b) @ c
        right = a @ (b @ c)

        assert left.value == right.value
        assert left.value == 77

    def test_associativity_large_numbers(self):
        a = MultInt(100)
        b = MultInt(200)
        c = MultInt(300)

        left = (a @ b) @ c
        right = a @ (b @ c)

        assert left.value == right.value
        assert left.value == 6000000


class TestMultIntIdentity:
    def test_left_identity_positive(self):
        identity = MultInt.identity()
        value = MultInt(42)

        result = identity @ value

        assert result.value == value.value
        assert result.value == 42

    def test_right_identity_positive(self):
        value = MultInt(42)
        identity = MultInt.identity()

        result = value @ identity

        assert result.value == value.value
        assert result.value == 42

    def test_left_identity_negative(self):
        identity = MultInt.identity()
        value = MultInt(-15)

        result = identity @ value

        assert result.value == value.value
        assert result.value == -15

    def test_right_identity_negative(self):
        value = MultInt(-15)
        identity = MultInt.identity()

        result = value @ identity

        assert result.value == value.value
        assert result.value == -15

    def test_left_identity_zero(self):
        identity = MultInt.identity()
        value = MultInt(0)

        result = identity @ value

        assert result.value == value.value
        assert result.value == 0

    def test_right_identity_zero(self):
        value = MultInt(0)
        identity = MultInt.identity()

        result = value @ identity

        assert result.value == value.value
        assert result.value == 0

    def test_identity_value_is_one(self):
        identity = MultInt.identity()

        assert identity.value == 1

    def test_identity_with_large_number(self):
        identity = MultInt.identity()
        value = MultInt(999999)

        left_result = identity @ value
        right_result = value @ identity

        assert left_result.value == value.value
        assert right_result.value == value.value
        assert left_result.value == 999999


class TestMultIntBasicOperations:
    def test_multiplication_positive_numbers(self):
        a = MultInt(6)
        b = MultInt(7)

        result = a @ b

        assert result.value == 42

    def test_multiplication_negative_numbers(self):
        a = MultInt(-4)
        b = MultInt(-5)

        result = a @ b

        assert result.value == 20

    def test_multiplication_mixed_signs(self):
        a = MultInt(8)
        b = MultInt(-3)

        result = a @ b

        assert result.value == -24

    def test_multiplication_with_zero(self):
        a = MultInt(100)
        b = MultInt(0)

        result = a @ b

        assert result.value == 0

    def test_repr(self):
        value = MultInt(42)

        assert repr(value) == "MultInt(42)"
        assert str(value) == "MultInt(42)"
