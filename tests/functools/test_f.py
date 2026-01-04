from katharos.functools.f import F


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
