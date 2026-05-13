import pytest

from katharos.types.maybe.maybe import _Nothing, is_nothing, nothing


class TestNothing:
    def test_nothing_singleton_instance(self):
        n1 = _Nothing()
        n2 = _Nothing()
        assert n1 is not n2

    def test_nothing_global_singleton(self):
        assert isinstance(nothing, _Nothing)

    def test_nothing_equality_with_itself(self):
        n = _Nothing()
        assert n == n

    def test_nothing_equality_with_another_nothing(self):
        n1 = _Nothing()
        n2 = _Nothing()
        assert n1 == n2

    def test_nothing_equality_with_global_nothing(self):
        n = _Nothing()
        assert n == nothing
        assert nothing == n

    def test_nothing_not_equal_to_none(self):
        n = _Nothing()
        assert n is not None
        assert None is not n

    def test_nothing_not_equal_to_other_types(self):
        n = _Nothing()
        assert n != 0
        assert n != ""
        assert n != []
        assert n != {}

    def test_nothing_repr(self):
        n = _Nothing()
        assert repr(n) == "Nothing()"
        assert repr(nothing) == "Nothing()"

    def test_nothing_str(self):
        n = _Nothing()
        assert str(n) == "Nothing()"

    def test_nothing_hash(self):
        n1 = _Nothing()
        n2 = _Nothing()
        assert hash(n1) == hash(n2)
        assert hash(n1) == hash(nothing)

    def test_nothing_hash_consistency(self):
        n = _Nothing()
        assert hash(n) == hash("Nothing")

    def test_nothing_hashable_in_set(self):
        n1 = _Nothing()
        n2 = _Nothing()
        s = {n1, n2, nothing}
        assert len(s) == 1

    def test_nothing_hashable_in_dict(self):
        n1 = _Nothing()
        n2 = _Nothing()
        d = {n1: 1, n2: 2, nothing: 3}
        assert len(d) == 1
        assert d[nothing] == 3

    def test_nothing_bool_is_false(self):
        n = _Nothing()
        assert not n
        assert not nothing
        assert bool(n) is False
        assert bool(nothing) is False

    def test_nothing_in_conditional(self):
        n = _Nothing()
        if n:
            pytest.fail("Nothing should be falsy")
        else:
            pass

    def test_is_nothing_with_nothing_instance(self):
        n = _Nothing()
        assert is_nothing(n)
        assert is_nothing(nothing)

    def test_is_nothing_with_other_types(self):
        assert not is_nothing(None)
        assert not is_nothing(0)
        assert not is_nothing("")
        assert not is_nothing([])
        assert not is_nothing({})
        assert not is_nothing(False)
        assert not is_nothing(True)
        assert not is_nothing("Nothing()")

    def test_nothing_type_check(self):
        n = _Nothing()
        assert isinstance(n, _Nothing)
        assert isinstance(nothing, _Nothing)
        assert not isinstance(None, _Nothing)
        assert not isinstance(0, _Nothing)
