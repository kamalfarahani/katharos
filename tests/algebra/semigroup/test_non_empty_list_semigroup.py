from katharos.algebra.semigroup.non_empty_list_semigroup import NonEmptyListSemigroup
from katharos.list.non_empty_list import NonEmptyList


class TestNonEmptyListSemigroup:
    def test_basic_combination(self):
        list1 = NonEmptyList(1, [2, 3])
        list2 = NonEmptyList(4, [5])

        sg1 = NonEmptyListSemigroup(list1)
        sg2 = NonEmptyListSemigroup(list2)

        result = sg1 @ sg2

        assert isinstance(result, NonEmptyListSemigroup)
        assert result.value == NonEmptyList(1, [2, 3, 4, 5])

    def test_associativity_with_integers(self):
        list1 = NonEmptyList(1, [2])
        list2 = NonEmptyList(3, [4])
        list3 = NonEmptyList(5, [6])

        sg1 = NonEmptyListSemigroup(list1)
        sg2 = NonEmptyListSemigroup(list2)
        sg3 = NonEmptyListSemigroup(list3)

        left_associated = (sg1 @ sg2) @ sg3
        right_associated = sg1 @ (sg2 @ sg3)

        assert left_associated.value == right_associated.value
        assert left_associated.value == NonEmptyList(1, [2, 3, 4, 5, 6])

    def test_associativity_with_strings(self):
        list1 = NonEmptyList("a", ["b"])
        list2 = NonEmptyList("c", ["d"])
        list3 = NonEmptyList("e", ["f"])

        sg1 = NonEmptyListSemigroup(list1)
        sg2 = NonEmptyListSemigroup(list2)
        sg3 = NonEmptyListSemigroup(list3)

        left_associated = (sg1 @ sg2) @ sg3
        right_associated = sg1 @ (sg2 @ sg3)

        assert left_associated.value == right_associated.value
        assert left_associated.value == NonEmptyList("a", ["b", "c", "d", "e", "f"])

    def test_associativity_with_single_elements(self):
        list1 = NonEmptyList(1, [])
        list2 = NonEmptyList(2, [])
        list3 = NonEmptyList(3, [])

        sg1 = NonEmptyListSemigroup(list1)
        sg2 = NonEmptyListSemigroup(list2)
        sg3 = NonEmptyListSemigroup(list3)

        left_associated = (sg1 @ sg2) @ sg3
        right_associated = sg1 @ (sg2 @ sg3)

        assert left_associated.value == right_associated.value
        assert left_associated.value == NonEmptyList(1, [2, 3])

    def test_associativity_with_longer_lists(self):
        list1 = NonEmptyList(1, [2, 3, 4, 5])
        list2 = NonEmptyList(6, [7, 8])
        list3 = NonEmptyList(9, [10, 11, 12])

        sg1 = NonEmptyListSemigroup(list1)
        sg2 = NonEmptyListSemigroup(list2)
        sg3 = NonEmptyListSemigroup(list3)

        left_associated = (sg1 @ sg2) @ sg3
        right_associated = sg1 @ (sg2 @ sg3)

        assert left_associated.value == right_associated.value
        assert left_associated.value == NonEmptyList(
            1, [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        )

    def test_associativity_with_four_operands(self):
        list1 = NonEmptyList(1, [])
        list2 = NonEmptyList(2, [])
        list3 = NonEmptyList(3, [])
        list4 = NonEmptyList(4, [])

        sg1 = NonEmptyListSemigroup(list1)
        sg2 = NonEmptyListSemigroup(list2)
        sg3 = NonEmptyListSemigroup(list3)
        sg4 = NonEmptyListSemigroup(list4)

        result1 = ((sg1 @ sg2) @ sg3) @ sg4
        result2 = (sg1 @ (sg2 @ sg3)) @ sg4
        result3 = sg1 @ ((sg2 @ sg3) @ sg4)
        result4 = sg1 @ (sg2 @ (sg3 @ sg4))
        result5 = (sg1 @ sg2) @ (sg3 @ sg4)

        expected = NonEmptyList(1, [2, 3, 4])

        assert result1.value == expected
        assert result2.value == expected
        assert result3.value == expected
        assert result4.value == expected
        assert result5.value == expected

    def test_associativity_with_mixed_types(self):
        list1 = NonEmptyList((1, "a"), [(2, "b")])
        list2 = NonEmptyList((3, "c"), [])
        list3 = NonEmptyList((4, "d"), [(5, "e")])

        sg1 = NonEmptyListSemigroup(list1)
        sg2 = NonEmptyListSemigroup(list2)
        sg3 = NonEmptyListSemigroup(list3)

        left_associated = (sg1 @ sg2) @ sg3
        right_associated = sg1 @ (sg2 @ sg3)

        assert left_associated.value == right_associated.value
        assert left_associated.value == NonEmptyList(
            (1, "a"), [(2, "b"), (3, "c"), (4, "d"), (5, "e")]
        )

    def test_value_property(self):
        list1 = NonEmptyList(1, [2, 3])
        sg = NonEmptyListSemigroup(list1)

        assert sg.value == list1
        assert sg.value.head == 1
        assert sg.value.tail == [2, 3]
