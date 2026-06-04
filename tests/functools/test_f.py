import pytest

from katharos.functools.f import F
from katharos.types.list import ImmutableList
from katharos.types.maybe import Maybe
from katharos.types.result import Result


class TestCompose:
    def test_compose_simple_functions(self):
        def add_one(x: int) -> int:
            return x + 1

        def multiply_by_two(x: int) -> int:
            return x * 2

        composed = F.compose(multiply_by_two)(add_one)
        assert composed(3) == 8

    def test_compose_string_functions(self):
        def to_upper(s: str) -> str:
            return s.upper()

        def add_exclamation(s: str) -> str:
            return s + "!"

        composed = F.compose(add_exclamation)(to_upper)
        assert composed("hello") == "HELLO!"

    def test_compose_with_type_conversion(self):
        def int_to_str(x: int) -> str:
            return str(x)

        def str_length(s: str) -> int:
            return len(s)

        composed = F.compose(str_length)(int_to_str)
        assert composed(12345) == 5

    def test_compose_multiple_compositions(self):
        def add_one(x: int) -> int:
            return x + 1

        def multiply_by_two(x: int) -> int:
            return x * 2

        def subtract_three(x: int) -> int:
            return x - 3

        composed = F.compose(subtract_three)(F.compose(multiply_by_two)(add_one))
        assert composed(5) == 9


class TestId:
    def test_id_with_int(self):
        assert F.id(42) == 42

    def test_id_with_string(self):
        assert F.id("hello") == "hello"

    def test_id_with_list(self):
        lst = [1, 2, 3]
        assert F.id(lst) == lst
        assert F.id(lst) is lst

    def test_id_with_none(self):
        assert F.id(None) is None

    def test_id_with_dict(self):
        d = {"key": "value"}
        assert F.id(d) == d
        assert F.id(d) is d


class TestFoldr:
    def test_foldr_sum(self):
        result = F.foldr(lambda x, acc: x + acc, 0, [1, 2, 3, 4])
        assert result == 10

    def test_foldr_empty_list(self):
        empty: list[int] = []
        result = F.foldr(lambda x, acc: x + acc, 0, empty)
        assert result == 0

    def test_foldr_single_element(self):
        result = F.foldr(lambda x, acc: x + acc, 5, [10])
        assert result == 15

    def test_foldr_string_concatenation(self):
        result = F.foldr(lambda x, acc: x + acc, "", ["a", "b", "c"])
        assert result == "abc"

    def test_foldr_list_construction(self):
        result = F.foldr(lambda x, acc: [x] + acc, [], [1, 2, 3])
        assert result == [1, 2, 3]

    def test_foldr_subtraction_order(self):
        result = F.foldr(lambda x, acc: x - acc, 0, [1, 2, 3])
        assert result == 2

    def test_foldr_with_generator(self):
        result = F.foldr(lambda x, acc: x + acc, 0, (x for x in range(1, 5)))
        assert result == 10

    def test_foldr_multiplication(self):
        result = F.foldr(lambda x, acc: x * acc, 1, [2, 3, 4])
        assert result == 24


class TestFoldl:
    def test_foldl_sum(self):
        result = F.foldl(lambda acc, x: acc + x, 0, [1, 2, 3, 4])
        assert result == 10

    def test_foldl_empty_list(self):
        empty: list[int] = []
        result = F.foldl(lambda acc, x: acc + x, 0, empty)
        assert result == 0

    def test_foldl_single_element(self):
        result = F.foldl(lambda acc, x: acc + x, 5, [10])
        assert result == 15

    def test_foldl_string_concatenation(self):
        result = F.foldl(lambda acc, x: acc + x, "", ["a", "b", "c"])
        assert result == "abc"

    def test_foldl_list_construction(self):
        result = F.foldl(lambda acc, x: acc + [x], [], [1, 2, 3])
        assert result == [1, 2, 3]

    def test_foldl_subtraction_order(self):
        result = F.foldl(lambda acc, x: acc - x, 0, [1, 2, 3])
        assert result == -6

    def test_foldl_with_generator(self):
        result = F.foldl(lambda acc, x: acc + x, 0, (x for x in range(1, 5)))
        assert result == 10

    def test_foldl_multiplication(self):
        result = F.foldl(lambda acc, x: acc * x, 1, [2, 3, 4])
        assert result == 24

    def test_foldl_reverse_list(self):
        result = F.foldl(lambda acc, x: [x] + acc, [], [1, 2, 3])
        assert result == [3, 2, 1]


class TestFoldComparison:
    def test_foldr_vs_foldl_associative_operation(self):
        foldr_result = F.foldr(lambda x, acc: x + acc, 0, [1, 2, 3, 4])
        foldl_result = F.foldl(lambda acc, x: acc + x, 0, [1, 2, 3, 4])
        assert foldr_result == foldl_result

    def test_foldr_vs_foldl_non_associative_operation(self):
        foldr_result = F.foldr(lambda x, acc: x - acc, 0, [1, 2, 3])
        foldl_result = F.foldl(lambda acc, x: acc - x, 0, [1, 2, 3])
        assert foldr_result != foldl_result
        assert foldr_result == 2
        assert foldl_result == -6


class TestCurry:
    def test_curry_basic_two_args(self):
        def add(x: int, y: int) -> int:
            return x + y

        curried_add = F.curry(add)
        assert curried_add(2)(3) == 5

    def test_curry_basic_three_args(self):
        def add(x: int, y: int, z: int) -> int:
            return x + y + z

        curried_add = F.curry(add)
        assert curried_add(1)(2)(3) == 6

    def test_curry_partial_application(self):
        def add(x: int, y: int, z: int) -> int:
            return x + y + z

        curried_add = F.curry(add)
        add_one = curried_add(1)
        assert add_one(2)(3) == 6

    def test_curry_multiple_partial_applications(self):
        def add(x: int, y: int, z: int) -> int:
            return x + y + z

        curried_add = F.curry(add)
        add_one = curried_add(1)
        add_one_two = add_one(2)
        assert add_one_two(3) == 6

    def test_curry_with_multiple_args_at_once(self):
        def add(x: int, y: int, z: int) -> int:
            return x + y + z

        curried_add = F.curry(add)
        assert curried_add(1, 2)(3) == 6
        assert curried_add(1)(2, 3) == 6
        assert curried_add(1, 2, 3) == 6

    def test_curry_zero_args_function(self):
        def get_value() -> int:
            return 42

        curried = F.curry(get_value)
        assert curried() == 42

    def test_curry_single_arg_function(self):
        def double(x: int) -> int:
            return x * 2

        curried_double = F.curry(double)
        assert curried_double(5) == 10

    def test_curry_with_strings(self):
        def concat(a: str, b: str, c: str) -> str:
            return a + b + c

        curried_concat = F.curry(concat)
        assert curried_concat("Hello")(" ")("World") == "Hello World"

    def test_curry_with_different_types(self):
        def format_message(name: str, age: int, active: bool) -> str:
            return f"{name} is {age} years old and {'active' if active else 'inactive'}"

        curried_format = F.curry(format_message)
        assert curried_format("Alice")(30)(True) == "Alice is 30 years old and active"

    def test_curry_reusability(self):
        def multiply(x: int, y: int, z: int) -> int:
            return x * y * z

        curried_multiply = F.curry(multiply)
        multiply_by_2 = curried_multiply(2)

        assert multiply_by_2(3)(4) == 24
        assert multiply_by_2(5)(6) == 60

    def test_curry_excess_args(self):
        def add(x: int, y: int) -> int:
            return x + y

        curried_add = F.curry(add)
        with pytest.raises(TypeError):
            curried_add(1, 2, 999)

    def test_curry_four_args(self):
        def combine(a: int, b: int, c: int, d: int) -> int:
            return a + b * c - d

        curried_combine = F.curry(combine)
        assert curried_combine(10)(5)(2)(3) == 17


class TestLiftA2:
    def test_lift_a2_maybe_both_just(self):
        result = F.lift_a2(lambda x, y: x + y, Maybe.Just(2), Maybe.Just(3))
        assert result == Maybe.Just(5)

    def test_lift_a2_maybe_first_nothing(self):
        result = F.lift_a2(lambda x, y: x + y, Maybe.Nothing(), Maybe.Just(3))
        assert result == Maybe.Nothing()

    def test_lift_a2_maybe_second_nothing(self):
        result = F.lift_a2(lambda x, y: x + y, Maybe.Just(2), Maybe.Nothing())
        assert result == Maybe.Nothing()

    def test_lift_a2_mixed_types(self):
        result = F.lift_a2(
            lambda name, age: f"{name} is {age}",
            Maybe.Just("Alice"),
            Maybe.Just(30),
        )
        assert result == Maybe.Just("Alice is 30")

    def test_lift_a2_result_both_success(self):
        result = F.lift_a2(lambda x, y: x * y, Result.Success(4), Result.Success(5))
        assert result == Result.Success(20)

    def test_lift_a2_result_short_circuits_on_failure(self):
        error = ValueError("boom")
        result = F.lift_a2(lambda x, y: x + y, Result.Failure(error), Result.Success(3))
        assert result == Result.Failure(error)

    def test_lift_a2_immutable_list_cartesian_product(self):
        result = F.lift_a2(
            lambda x, y: (x, y),
            ImmutableList([1, 2]),
            ImmutableList(["a", "b"]),
        )
        assert result == ImmutableList([(1, "a"), (1, "b"), (2, "a"), (2, "b")])

    def test_lift_a2_immutable_list_empty(self):
        result = F.lift_a2(lambda x, y: x + y, ImmutableList([]), ImmutableList([1, 2]))
        assert result == ImmutableList([])

    def test_lift_a2_does_not_mutate_arguments(self):
        fa = Maybe.Just(2)
        fb = Maybe.Just(3)
        F.lift_a2(lambda x, y: x + y, fa, fb)
        assert fa == Maybe.Just(2)
        assert fb == Maybe.Just(3)


class TestLiftA3:
    def test_lift_a3_maybe_all_just(self):
        result = F.lift_a3(
            lambda x, y, z: x + y + z,
            Maybe.Just(1),
            Maybe.Just(2),
            Maybe.Just(3),
        )
        assert result == Maybe.Just(6)

    def test_lift_a3_maybe_first_nothing(self):
        result = F.lift_a3(
            lambda x, y, z: x + y + z,
            Maybe.Nothing(),
            Maybe.Just(2),
            Maybe.Just(3),
        )
        assert result == Maybe.Nothing()

    def test_lift_a3_maybe_middle_nothing(self):
        result = F.lift_a3(
            lambda x, y, z: x + y + z,
            Maybe.Just(1),
            Maybe.Nothing(),
            Maybe.Just(3),
        )
        assert result == Maybe.Nothing()

    def test_lift_a3_maybe_last_nothing(self):
        result = F.lift_a3(
            lambda x, y, z: x + y + z,
            Maybe.Just(1),
            Maybe.Just(2),
            Maybe.Nothing(),
        )
        assert result == Maybe.Nothing()

    def test_lift_a3_preserves_argument_order(self):
        result = F.lift_a3(
            lambda x, y, z: f"{x}-{y}-{z}",
            Maybe.Just("a"),
            Maybe.Just("b"),
            Maybe.Just("c"),
        )
        assert result == Maybe.Just("a-b-c")

    def test_lift_a3_result_all_success(self):
        result = F.lift_a3(
            lambda x, y, z: x + y + z,
            Result.Success(1),
            Result.Success(2),
            Result.Success(3),
        )
        assert result == Result.Success(6)

    def test_lift_a3_result_short_circuits_on_failure(self):
        error = ValueError("boom")
        result = F.lift_a3(
            lambda x, y, z: x + y + z,
            Result.Success(1),
            Result.Failure(error),
            Result.Success(3),
        )
        assert result == Result.Failure(error)

    def test_lift_a3_immutable_list_cartesian_product(self):
        result = F.lift_a3(
            lambda x, y, z: x + y + z,
            ImmutableList([1, 2]),
            ImmutableList([10]),
            ImmutableList([100, 200]),
        )
        assert result == ImmutableList([111, 211, 112, 212])
