from katharos.types import Maybe


class TestMaybeEquality:
    def test_just_equals_just_same_value(self):
        m1 = Maybe.Just(5)
        m2 = Maybe.Just(5)
        assert m1 == m2

    def test_just_equals_just_different_value(self):
        m1 = Maybe.Just(5)
        m2 = Maybe.Just(10)
        assert m1 != m2

    def test_nothing_equals_nothing(self):
        m1 = Maybe.Nothing()
        m2 = Maybe.Nothing()
        assert m1 == m2

    def test_just_not_equals_nothing(self):
        m1 = Maybe.Just(5)
        m2 = Maybe.Nothing()
        assert m1 != m2
        assert m2 != m1

    def test_just_not_equals_none(self):
        m = Maybe.Just(5)
        assert m is not None

    def test_nothing_not_equals_none(self):
        m = Maybe.Nothing()
        assert m is not None

    def test_maybe_not_equals_other_types(self):
        m = Maybe.Just(5)
        assert m != 5
        assert m != "5"
        assert m != [5]
        assert m != {"value": 5}

    def test_just_equals_with_complex_types(self):
        m1 = Maybe.Just([1, 2, 3])
        m2 = Maybe.Just([1, 2, 3])
        assert m1 == m2

    def test_just_equals_with_nested_maybe(self):
        m1 = Maybe.Just(Maybe.Just(5))
        m2 = Maybe.Just(Maybe.Just(5))
        assert m1 == m2

    def test_equality_reflexive(self):
        m = Maybe.Just(42)
        assert m == m

    def test_equality_symmetric(self):
        m1 = Maybe.Just(42)
        m2 = Maybe.Just(42)
        assert m1 == m2
        assert m2 == m1


class TestMaybeHash:
    def test_just_hash_same_value(self):
        m1 = Maybe.Just(5)
        m2 = Maybe.Just(5)
        assert hash(m1) == hash(m2)

    def test_just_hash_different_value(self):
        m1 = Maybe.Just(5)
        m2 = Maybe.Just(10)
        assert hash(m1) != hash(m2)

    def test_nothing_hash_consistent(self):
        m1 = Maybe.Nothing()
        m2 = Maybe.Nothing()
        assert hash(m1) == hash(m2)

    def test_just_hashable_in_set(self):
        m1 = Maybe.Just(5)
        m2 = Maybe.Just(5)
        m3 = Maybe.Just(10)
        s = {m1, m2, m3}
        assert len(s) == 2

    def test_nothing_hashable_in_set(self):
        m1 = Maybe.Nothing()
        m2 = Maybe.Nothing()
        s = {m1, m2}
        assert len(s) == 1

    def test_maybe_hashable_in_dict(self):
        m1 = Maybe.Just(5)
        m2 = Maybe.Just(10)
        m3 = Maybe.Nothing()
        d = {m1: "five", m2: "ten", m3: "nothing"}
        assert len(d) == 3
        assert d[Maybe.Just(5)] == "five"
        assert d[Maybe.Nothing()] == "nothing"

    def test_hash_consistency_with_equality(self):
        m1 = Maybe.Just(42)
        m2 = Maybe.Just(42)
        if m1 == m2:
            assert hash(m1) == hash(m2)

    def test_just_hash_with_string(self):
        m1 = Maybe.Just("hello")
        m2 = Maybe.Just("hello")
        assert hash(m1) == hash(m2)

    def test_just_hash_with_tuple(self):
        m1 = Maybe.Just((1, 2, 3))
        m2 = Maybe.Just((1, 2, 3))
        assert hash(m1) == hash(m2)


class TestMaybeRepr:
    def test_just_repr(self):
        m = Maybe.Just(5)
        assert repr(m) == "Just(5)"

    def test_nothing_repr(self):
        m = Maybe.Nothing()
        assert repr(m) == "Nothing()"

    def test_just_repr_with_string(self):
        m = Maybe.Just("hello")
        assert repr(m) == "Just('hello')"

    def test_just_repr_with_list(self):
        m = Maybe.Just([1, 2, 3])
        assert repr(m) == "Just([1, 2, 3])"

    def test_just_repr_with_nested_maybe(self):
        m = Maybe.Just(Maybe.Just(5))
        assert repr(m) == "Just(Just(5))"

    def test_just_repr_with_none_value(self):
        m = Maybe.Just(None)
        assert repr(m) == "Just(None)"

    def test_str_same_as_repr(self):
        m1 = Maybe.Just(42)
        m2 = Maybe.Nothing()
        assert str(m1) == repr(m1)
        assert str(m2) == repr(m2)


class TestMaybeTypeChecks:
    def test_just_isinstance_maybe(self):
        m = Maybe.Just(5)
        assert isinstance(m, Maybe)

    def test_nothing_isinstance_maybe(self):
        m = Maybe.Nothing()
        assert isinstance(m, Maybe)

    def test_just_is_just(self):
        m = Maybe.Just(5)
        assert m.is_just()
        assert not m.is_nothing()

    def test_nothing_is_nothing(self):
        m = Maybe.Nothing()
        assert m.is_nothing()
        assert not m.is_just()

    def test_just_with_zero_is_just(self):
        m = Maybe.Just(0)
        assert m.is_just()
        assert not m.is_nothing()

    def test_just_with_empty_string_is_just(self):
        m = Maybe.Just("")
        assert m.is_just()
        assert not m.is_nothing()

    def test_just_with_false_is_just(self):
        m = Maybe.Just(False)
        assert m.is_just()
        assert not m.is_nothing()

    def test_just_with_none_is_just(self):
        m = Maybe.Just(None)
        assert m.is_just()
        assert not m.is_nothing()
