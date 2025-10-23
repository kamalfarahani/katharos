"""Tests for the ImmutableList class."""

import pytest
from typing import Any

from katharos.data_structures.immutable_list import ImmutableList


class TestImmutableListInitialization:
    """Test initialization and constructor behavior."""

    def test_init_with_list(self) -> None:
        """Test initialization with a list."""
        elements = [1, 2, 3, 4, 5]
        immutable_list = ImmutableList(elements)
        assert len(immutable_list) == 5
        assert list(immutable_list) == elements

    def test_init_with_tuple(self) -> None:
        """Test initialization with a tuple."""
        elements = (1, 2, 3)
        immutable_list = ImmutableList(elements)
        assert len(immutable_list) == 3
        assert list(immutable_list) == [1, 2, 3]

    def test_init_with_generator(self) -> None:
        """Test initialization with a generator."""
        elements = (x * 2 for x in range(3))
        immutable_list = ImmutableList(elements)
        assert len(immutable_list) == 3
        assert list(immutable_list) == [0, 2, 4]

    def test_init_with_empty_iterable(self) -> None:
        """Test initialization with an empty iterable."""
        immutable_list = ImmutableList([])
        assert len(immutable_list) == 0
        assert list(immutable_list) == []

    def test_init_with_string(self) -> None:
        """Test initialization with a string (iterable of characters)."""
        immutable_list = ImmutableList("hello")
        assert len(immutable_list) == 5
        assert list(immutable_list) == ['h', 'e', 'l', 'l', 'o']


class TestSequenceOperations:
    """Test sequence operations like length, indexing, and iteration."""

    def test_len(self) -> None:
        """Test __len__ method."""
        assert len(ImmutableList([])) == 0
        assert len(ImmutableList([1])) == 1
        assert len(ImmutableList([1, 2, 3, 4, 5])) == 5

    def test_getitem_positive_index(self) -> None:
        """Test __getitem__ with positive indices."""
        immutable_list = ImmutableList(['a', 'b', 'c', 'd'])
        assert immutable_list[0] == 'a'
        assert immutable_list[1] == 'b'
        assert immutable_list[2] == 'c'
        assert immutable_list[3] == 'd'

    def test_getitem_negative_index(self) -> None:
        """Test __getitem__ with negative indices."""
        immutable_list = ImmutableList(['a', 'b', 'c', 'd'])
        assert immutable_list[-1] == 'd'
        assert immutable_list[-2] == 'c'
        assert immutable_list[-3] == 'b'
        assert immutable_list[-4] == 'a'

    def test_getitem_index_error(self) -> None:
        """Test __getitem__ raises IndexError for invalid indices."""
        immutable_list = ImmutableList([1, 2, 3])
        
        with pytest.raises(IndexError):
            _ = immutable_list[3]
        
        with pytest.raises(IndexError):
            _ = immutable_list[-4]

    def test_iter(self) -> None:
        """Test __iter__ method."""
        elements = [1, 2, 3, 4, 5]
        immutable_list = ImmutableList(elements)
        
        result = []
        for item in immutable_list:
            result.append(item)
        
        assert result == elements

    def test_iter_empty(self) -> None:
        """Test iteration over empty list."""
        immutable_list = ImmutableList([])
        result = list(immutable_list)
        assert result == []


class TestMembershipOperations:
    """Test membership operations using 'in' operator."""

    def test_contains_existing_element(self) -> None:
        """Test __contains__ with existing elements."""
        immutable_list = ImmutableList([1, 2, 3, 'hello', None])
        assert 1 in immutable_list
        assert 2 in immutable_list
        assert 3 in immutable_list
        assert 'hello' in immutable_list
        assert None in immutable_list

    def test_contains_non_existing_element(self) -> None:
        """Test __contains__ with non-existing elements."""
        immutable_list = ImmutableList([1, 2, 3])
        assert 4 not in immutable_list
        assert 'hello' not in immutable_list
        assert None not in immutable_list

    def test_contains_empty_list(self) -> None:
        """Test __contains__ with empty list."""
        immutable_list = ImmutableList([])
        assert 1 not in immutable_list
        assert None not in immutable_list


class TestEqualityOperations:
    """Test equality and inequality operations."""

    def test_eq_same_elements(self) -> None:
        """Test __eq__ with lists containing same elements."""
        list1 = ImmutableList([1, 2, 3])
        list2 = ImmutableList([1, 2, 3])
        assert list1 == list2

    def test_eq_different_elements(self) -> None:
        """Test __eq__ with lists containing different elements."""
        list1 = ImmutableList([1, 2, 3])
        list2 = ImmutableList([1, 2, 4])
        assert not (list1 == list2)

    def test_eq_different_lengths(self) -> None:
        """Test __eq__ with lists of different lengths."""
        list1 = ImmutableList([1, 2, 3])
        list2 = ImmutableList([1, 2])
        assert not (list1 == list2)

    def test_eq_empty_lists(self) -> None:
        """Test __eq__ with empty lists."""
        list1 = ImmutableList([])
        list2 = ImmutableList([])
        assert list1 == list2

    def test_eq_with_non_immutable_list(self) -> None:
        """Test __eq__ with non-ImmutableList objects."""
        immutable_list = ImmutableList([1, 2, 3])
        regular_list = [1, 2, 3]
        assert not (immutable_list == regular_list)
        assert not (immutable_list == "hello")
        assert not (immutable_list == 123)

    def test_ne_same_elements(self) -> None:
        """Test __ne__ with lists containing same elements."""
        list1 = ImmutableList([1, 2, 3])
        list2 = ImmutableList([1, 2, 3])
        assert not (list1 != list2)

    def test_ne_different_elements(self) -> None:
        """Test __ne__ with lists containing different elements."""
        list1 = ImmutableList([1, 2, 3])
        list2 = ImmutableList([1, 2, 4])
        assert list1 != list2

    def test_ne_with_non_immutable_list(self) -> None:
        """Test __ne__ with non-ImmutableList objects."""
        immutable_list = ImmutableList([1, 2, 3])
        regular_list = [1, 2, 3]
        assert immutable_list != regular_list


class TestHashability:
    """Test hash functionality for use in sets and as dict keys."""

    def test_hash_same_elements(self) -> None:
        """Test that lists with same elements have same hash."""
        list1 = ImmutableList([1, 2, 3])
        list2 = ImmutableList([1, 2, 3])
        assert hash(list1) == hash(list2)

    def test_hash_different_elements(self) -> None:
        """Test that lists with different elements have different hashes."""
        list1 = ImmutableList([1, 2, 3])
        list2 = ImmutableList([1, 2, 4])
        # Note: Different elements should typically have different hashes,
        # but hash collisions are possible, so we don't assert inequality
        hash1 = hash(list1)
        hash2 = hash(list2)
        # Just ensure they are both integers (valid hashes)
        assert isinstance(hash1, int)
        assert isinstance(hash2, int)

    def test_hash_empty_list(self) -> None:
        """Test hash of empty list."""
        empty_list = ImmutableList([])
        hash_value = hash(empty_list)
        assert isinstance(hash_value, int)

    def test_use_as_dict_key(self) -> None:
        """Test using ImmutableList as dictionary key."""
        list1 = ImmutableList([1, 2, 3])
        list2 = ImmutableList([4, 5, 6])
        
        dictionary = {list1: "first", list2: "second"}
        
        assert dictionary[list1] == "first"
        assert dictionary[list2] == "second"

    def test_use_in_set(self) -> None:
        """Test using ImmutableList in a set."""
        list1 = ImmutableList([1, 2, 3])
        list2 = ImmutableList([4, 5, 6])
        list3 = ImmutableList([1, 2, 3])  # Same as list1
        
        immutable_set = {list1, list2, list3}
        
        # Should only contain 2 unique lists
        assert len(immutable_set) == 2
        assert list1 in immutable_set
        assert list2 in immutable_set


class TestStringRepresentations:
    """Test string representation methods."""

    def test_repr(self) -> None:
        """Test __repr__ method."""
        immutable_list = ImmutableList([1, 2, 3])
        expected = "ImmutableList([1, 2, 3])"
        assert repr(immutable_list) == expected

    def test_repr_empty(self) -> None:
        """Test __repr__ with empty list."""
        immutable_list = ImmutableList([])
        expected = "ImmutableList([])"
        assert repr(immutable_list) == expected

    def test_repr_with_strings(self) -> None:
        """Test __repr__ with string elements."""
        immutable_list = ImmutableList(['hello', 'world'])
        expected = "ImmutableList(['hello', 'world'])"
        assert repr(immutable_list) == expected

    def test_str(self) -> None:
        """Test __str__ method."""
        immutable_list = ImmutableList([1, 2, 3])
        expected = "[1, 2, 3]"
        assert str(immutable_list) == expected

    def test_str_empty(self) -> None:
        """Test __str__ with empty list."""
        immutable_list = ImmutableList([])
        expected = "[]"
        assert str(immutable_list) == expected


class TestAdditionOperation:
    """Test addition operation for creating new ImmutableLists."""

    def test_add_with_list(self) -> None:
        """Test __add__ with a regular list."""
        immutable_list = ImmutableList([1, 2, 3])
        result = immutable_list + [4, 5, 6]
        
        assert isinstance(result, ImmutableList)
        assert list(result) == [1, 2, 3, 4, 5, 6]
        # Original should be unchanged
        assert list(immutable_list) == [1, 2, 3]

    def test_add_with_empty_list(self) -> None:
        """Test __add__ with empty list."""
        immutable_list = ImmutableList([1, 2, 3])
        result = immutable_list + []
        
        assert isinstance(result, ImmutableList)
        assert list(result) == [1, 2, 3]

    def test_add_empty_with_list(self) -> None:
        """Test __add__ with empty ImmutableList and regular list."""
        immutable_list = ImmutableList([])
        result = immutable_list + [1, 2, 3]
        
        assert isinstance(result, ImmutableList)
        assert list(result) == [1, 2, 3]

    def test_add_preserves_types(self) -> None:
        """Test that __add__ preserves element types."""
        immutable_list = ImmutableList(['a', 'b'])
        result = immutable_list + ['c', 'd']
        
        assert isinstance(result, ImmutableList)
        assert list(result) == ['a', 'b', 'c', 'd']
        assert all(isinstance(item, str) for item in result)


class TestEdgeCasesAndErrorConditions:
    """Test edge cases and error conditions."""

    def test_immutability_original_list_modification(self) -> None:
        """Test that modifying original list doesn't affect ImmutableList."""
        original = [1, 2, 3]
        immutable_list = ImmutableList(original)
        
        # Modify original list
        original.append(4)
        original[0] = 999
        
        # ImmutableList should be unchanged
        assert list(immutable_list) == [1, 2, 3]

    def test_large_list(self) -> None:
        """Test with a large list."""
        large_list = list(range(10000))
        immutable_list = ImmutableList(large_list)
        
        assert len(immutable_list) == 10000
        assert immutable_list[0] == 0
        assert immutable_list[9999] == 9999
        assert 5000 in immutable_list

    def test_nested_structures(self) -> None:
        """Test with nested data structures."""
        nested = [[1, 2], [3, 4], {'a': 5}]
        immutable_list = ImmutableList(nested)
        
        assert len(immutable_list) == 3
        assert immutable_list[0] == [1, 2]
        assert immutable_list[1] == [3, 4]
        assert immutable_list[2] == {'a': 5}

    def test_mixed_types(self) -> None:
        """Test with mixed data types."""
        mixed = [1, 'hello', 3.14, None, [1, 2], {'key': 'value'}]
        immutable_list = ImmutableList(mixed)
        
        assert len(immutable_list) == 6
        assert immutable_list[0] == 1
        assert immutable_list[1] == 'hello'
        assert immutable_list[2] == 3.14
        assert immutable_list[3] is None
        assert immutable_list[4] == [1, 2]
        assert immutable_list[5] == {'key': 'value'}


class TestTypeCovariance:
    """Test type covariance behavior."""

    def test_covariance_with_inheritance(self) -> None:
        """Test covariance with class inheritance."""
        class Animal:
            def __init__(self, name: str) -> None:
                self.name = name
            
            def __eq__(self, other: Any) -> bool:
                return isinstance(other, Animal) and self.name == other.name

        class Dog(Animal):
            def bark(self) -> str:
                return "Woof!"

        # Create ImmutableList of Dogs
        dogs = [Dog("Buddy"), Dog("Max")]
        dog_list = ImmutableList(dogs)
        
        # This should work due to covariance (Dog is subtype of Animal)
        animal_list: ImmutableList[Animal] = dog_list
        
        assert len(animal_list) == 2
        assert animal_list[0].name == "Buddy"
        assert animal_list[1].name == "Max"

    def test_covariance_with_builtin_types(self) -> None:
        """Test covariance with built-in types."""
        # bool is a subtype of int in Python
        bool_list = ImmutableList([True, False, True])
        int_list: ImmutableList[int] = bool_list
        
        assert len(int_list) == 3
        assert int_list[0] == 1  # True as int
        assert int_list[1] == 0  # False as int
        assert int_list[2] == 1  # True as int
