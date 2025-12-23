import pytest

from katharos.list.non_empty_list import NonEmptyList


class TestNonEmptyListInit:
    def test_init_with_head_only(self):
        lst = NonEmptyList(1, [])
        assert len(lst) == 1
        assert lst.head == 1
        assert lst.tail == []

    def test_init_with_head_and_tail(self):
        lst = NonEmptyList(1, [2, 3, 4])
        assert len(lst) == 4
        assert lst.head == 1
        assert lst.tail == [2, 3, 4]

    def test_init_with_different_types(self):
        str_list = NonEmptyList("a", ["b", "c"])
        assert str_list.head == "a"
        assert str_list.tail == ["b", "c"]

        float_list = NonEmptyList(1.5, [2.5, 3.5])
        assert float_list.head == 1.5
        assert float_list.tail == [2.5, 3.5]


class TestNonEmptyListProperties:
    def test_head_property(self):
        lst = NonEmptyList(10, [20, 30])
        assert lst.head == 10

    def test_tail_property_empty(self):
        lst = NonEmptyList(1, [])
        assert lst.tail == []

    def test_tail_property_with_elements(self):
        lst = NonEmptyList(1, [2, 3, 4, 5])
        assert lst.tail == [2, 3, 4, 5]

    def test_tail_is_copy(self):
        lst = NonEmptyList(1, [2, 3])
        tail = lst.tail
        tail.append(4)
        assert lst.tail == [2, 3]


class TestNonEmptyListEquality:
    def test_equality_same_elements(self):
        lst1 = NonEmptyList(1, [2, 3])
        lst2 = NonEmptyList(1, [2, 3])
        assert lst1 == lst2

    def test_equality_single_element(self):
        lst1 = NonEmptyList(42, [])
        lst2 = NonEmptyList(42, [])
        assert lst1 == lst2

    def test_inequality_different_head(self):
        lst1 = NonEmptyList(1, [2, 3])
        lst2 = NonEmptyList(2, [2, 3])
        assert lst1 != lst2

    def test_inequality_different_tail(self):
        lst1 = NonEmptyList(1, [2, 3])
        lst2 = NonEmptyList(1, [2, 4])
        assert lst1 != lst2

    def test_inequality_different_length(self):
        lst1 = NonEmptyList(1, [2, 3])
        lst2 = NonEmptyList(1, [2])
        assert lst1 != lst2

    def test_inequality_with_non_nonemptylist(self):
        lst = NonEmptyList(1, [2, 3])
        assert lst != [1, 2, 3]
        assert lst != (1, 2, 3)
        assert lst != "123"
        assert lst is not None
        assert lst != 123


class TestNonEmptyListHash:
    def test_hash_consistent(self):
        lst = NonEmptyList(1, [2, 3])
        hash1 = hash(lst)
        hash2 = hash(lst)
        assert hash1 == hash2

    def test_hash_equal_lists_same_hash(self):
        lst1 = NonEmptyList(1, [2, 3])
        lst2 = NonEmptyList(1, [2, 3])
        assert hash(lst1) == hash(lst2)

    def test_hash_different_lists_different_hash(self):
        lst1 = NonEmptyList(1, [2, 3])
        lst2 = NonEmptyList(1, [2, 4])
        assert hash(lst1) != hash(lst2)

    def test_hashable_in_set(self):
        lst1 = NonEmptyList(1, [2, 3])
        lst2 = NonEmptyList(4, [5, 6])
        lst3 = NonEmptyList(1, [2, 3])

        s = {lst1, lst2, lst3}
        assert len(s) == 2

    def test_hashable_as_dict_key(self):
        lst1 = NonEmptyList(1, [2, 3])
        lst2 = NonEmptyList(4, [5, 6])

        d = {lst1: "first", lst2: "second"}
        assert d[lst1] == "first"
        assert d[lst2] == "second"


class TestNonEmptyListAddition:
    def test_add_with_list(self):
        lst1 = NonEmptyList(1, [2, 3])
        result = lst1 + [4, 5]
        assert isinstance(result, NonEmptyList)
        assert result.head == 1
        assert result.tail == [2, 3, 4, 5]

    def test_add_with_empty_list(self):
        lst1 = NonEmptyList(1, [2, 3])
        result = lst1 + []
        assert isinstance(result, NonEmptyList)
        assert result.head == 1
        assert result.tail == [2, 3]

    def test_add_with_tuple(self):
        lst1 = NonEmptyList(1, [2])
        result = lst1 + (3, 4, 5)
        assert isinstance(result, NonEmptyList)
        assert result.head == 1
        assert result.tail == [2, 3, 4, 5]

    def test_add_with_another_nonemptylist(self):
        lst1 = NonEmptyList(1, [2])
        lst2 = NonEmptyList(3, [4, 5])
        result = lst1 + lst2
        assert isinstance(result, NonEmptyList)
        assert result.head == 1
        assert result.tail == [2, 3, 4, 5]

    def test_add_preserves_original(self):
        lst1 = NonEmptyList(1, [2, 3])
        _ = lst1 + [4, 5]
        assert lst1.head == 1
        assert lst1.tail == [2, 3]
        assert len(lst1) == 3

    def test_add_single_element_list(self):
        lst1 = NonEmptyList(1, [])
        result = lst1 + [2, 3]
        assert result.head == 1
        assert result.tail == [2, 3]


class TestNonEmptyListRepr:
    def test_repr_single_element(self):
        lst = NonEmptyList(1, [])
        assert repr(lst) == "NonEmptyList([1])"

    def test_repr_multiple_elements(self):
        lst = NonEmptyList(1, [2, 3, 4])
        assert repr(lst) == "NonEmptyList([1, 2, 3, 4])"

    def test_repr_with_strings(self):
        lst = NonEmptyList("a", ["b", "c"])
        assert repr(lst) == "NonEmptyList(['a', 'b', 'c'])"


class TestNonEmptyListStr:
    def test_str_single_element(self):
        lst = NonEmptyList(1, [])
        assert str(lst) == "[1]"

    def test_str_multiple_elements(self):
        lst = NonEmptyList(1, [2, 3, 4])
        assert str(lst) == "[1, 2, 3, 4]"


class TestNonEmptyListLen:
    def test_len_single_element(self):
        lst = NonEmptyList(1, [])
        assert len(lst) == 1

    def test_len_multiple_elements(self):
        lst = NonEmptyList(1, [2, 3, 4, 5])
        assert len(lst) == 5


class TestNonEmptyListIter:
    def test_iter_single_element(self):
        lst = NonEmptyList(1, [])
        elements = list(lst)
        assert elements == [1]

    def test_iter_multiple_elements(self):
        lst = NonEmptyList(1, [2, 3, 4])
        elements = list(lst)
        assert elements == [1, 2, 3, 4]

    def test_iter_in_for_loop(self):
        lst = NonEmptyList(1, [2, 3])
        result = []
        for item in lst:
            result.append(item * 2)
        assert result == [2, 4, 6]


class TestNonEmptyListGetItem:
    def test_getitem_first_element(self):
        lst = NonEmptyList(10, [20, 30])
        assert lst[0] == 10

    def test_getitem_middle_element(self):
        lst = NonEmptyList(10, [20, 30, 40])
        assert lst[1] == 20
        assert lst[2] == 30

    def test_getitem_last_element(self):
        lst = NonEmptyList(10, [20, 30])
        assert lst[2] == 30

    def test_getitem_negative_index(self):
        lst = NonEmptyList(10, [20, 30])
        assert lst[-1] == 30
        assert lst[-2] == 20
        assert lst[-3] == 10

    def test_getitem_out_of_range(self):
        lst = NonEmptyList(1, [2, 3])
        with pytest.raises(IndexError):
            _ = lst[10]

    def test_getitem_negative_out_of_range(self):
        lst = NonEmptyList(1, [2, 3])
        with pytest.raises(IndexError):
            _ = lst[-10]


class TestNonEmptyListContains:
    def test_contains_head(self):
        lst = NonEmptyList(1, [2, 3])
        assert 1 in lst

    def test_contains_tail_element(self):
        lst = NonEmptyList(1, [2, 3])
        assert 2 in lst
        assert 3 in lst

    def test_contains_not_present(self):
        lst = NonEmptyList(1, [2, 3])
        assert 4 not in lst
        assert 0 not in lst

    def test_contains_with_strings(self):
        lst = NonEmptyList("hello", ["world", "test"])
        assert "hello" in lst
        assert "world" in lst
        assert "foo" not in lst

    def test_contains_single_element(self):
        lst = NonEmptyList(42, [])
        assert 42 in lst
        assert 0 not in lst
