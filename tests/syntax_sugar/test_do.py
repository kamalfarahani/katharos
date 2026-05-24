from typing import cast

from katharos.syntax_sugar.do import DoBlock, do
from katharos.types import ImmutableList, Maybe, Result


class TestDoWithMaybe:
    def test_two_just_values_are_combined(self):
        @do(Maybe)
        def computation() -> DoBlock[int]:
            x: int = yield Maybe.Just(3)
            y: int = yield Maybe.Just(4)
            return x + y

        assert computation() == Maybe.Just(7)

    def test_first_nothing_short_circuits(self):
        @do(Maybe)
        def computation() -> DoBlock[int]:
            x: int = yield Maybe.Nothing()
            y: int = yield Maybe.Just(4)
            return x + y

        assert computation() == Maybe.Nothing()

    def test_second_nothing_short_circuits(self):
        @do(Maybe)
        def computation() -> DoBlock[int]:
            x: int = yield Maybe.Just(3)
            y: int = yield Maybe.Nothing()
            return x + y

        assert computation() == Maybe.Nothing()

    def test_single_just_value(self):
        @do(Maybe)
        def computation() -> DoBlock[int]:
            x: int = yield Maybe.Just(10)
            return x * 2

        assert computation() == Maybe.Just(20)

    def test_single_nothing(self):
        @do(Maybe)
        def computation() -> DoBlock[int]:
            x: int = yield Maybe.Nothing()
            return x * 2

        assert computation() == Maybe.Nothing()

    def test_three_just_values(self):
        @do(Maybe)
        def computation() -> DoBlock[int]:
            x: int = yield Maybe.Just(1)
            y: int = yield Maybe.Just(2)
            z: int = yield Maybe.Just(3)
            return x + y + z

        assert computation() == Maybe.Just(6)

    def test_middle_nothing_short_circuits(self):
        @do(Maybe)
        def computation() -> DoBlock[int]:
            x: int = yield Maybe.Just(1)
            y: int = yield Maybe.Nothing()
            z: int = yield Maybe.Just(3)
            return x + y + z

        assert computation() == Maybe.Nothing()

    def test_intermediate_value_used_in_subsequent_yield(self):
        @do(Maybe)
        def computation() -> DoBlock[int]:
            x: int = yield Maybe.Just(3)
            y: int = yield Maybe.Just(x + 1)
            return x + y

        assert computation() == Maybe.Just(7)

    def test_different_inner_types(self):
        @do(Maybe)
        def computation() -> DoBlock[int]:
            x: int = yield Maybe.Just(3)
            y: str = yield Maybe.Just("hi")
            return x + len(y)

        assert computation() == Maybe.Just(5)


class TestDoWithResult:
    def test_two_successes_are_combined(self):
        @do(Result)
        def computation() -> DoBlock[int]:
            x: int = yield Result.Success(10)
            y: int = yield Result.Success(5)
            return x - y

        assert computation() == Result.Success(5)

    def test_first_failure_short_circuits(self):
        err = ValueError("bad input")

        @do(Result)
        def computation() -> DoBlock[int]:
            x: int = yield Result.Failure(err)
            y: int = yield Result.Success(5)
            return x + y

        result = cast(Result, computation())
        assert result.is_failure()
        assert result.error is err

    def test_second_failure_short_circuits(self):
        err = TypeError("wrong type")

        @do(Result)
        def computation() -> DoBlock[int]:
            x: int = yield Result.Success(10)
            y: int = yield Result.Failure(err)
            return x + y

        result = cast(Result, computation())
        assert result.is_failure()
        assert result.error is err

    def test_single_success(self):
        @do(Result)
        def computation() -> DoBlock[int]:
            x: int = yield Result.Success(7)
            return x**2

        assert computation() == Result.Success(49)

    def test_single_failure(self):
        err = RuntimeError("oops")

        @do(Result)
        def computation() -> DoBlock[int]:
            x: int = yield Result.Failure(err)
            return x + 1

        result = cast(Result, computation())
        assert result.is_failure()
        assert result.error is err

    def test_three_successes(self):
        @do(Result)
        def computation() -> DoBlock[int]:
            x: int = yield Result.Success(2)
            y: int = yield Result.Success(3)
            z: int = yield Result.Success(4)
            return x * y * z

        assert computation() == Result.Success(24)

    def test_intermediate_value_used_in_subsequent_yield(self):
        @do(Result)
        def computation() -> DoBlock[int]:
            x: int = yield Result.Success(10)
            y: int = yield Result.Success(x * 2)
            return x + y

        assert computation() == Result.Success(30)


class TestDoWithImmutableList:
    def test_cartesian_product_of_two_lists(self):
        @do(ImmutableList)
        def computation() -> DoBlock[int]:
            x: int = yield ImmutableList([1, 2])
            y: int = yield ImmutableList([10, 20])
            return x + y

        assert computation() == ImmutableList([11, 21, 12, 22])

    def test_empty_first_list_yields_empty(self):
        @do(ImmutableList)
        def computation() -> DoBlock[int]:
            x: int = yield ImmutableList([])
            y: int = yield ImmutableList([1, 2, 3])
            return x + y

        assert computation() == ImmutableList([])

    def test_empty_second_list_yields_empty(self):
        @do(ImmutableList)
        def computation() -> DoBlock[int]:
            x: int = yield ImmutableList([1, 2, 3])
            y: int = yield ImmutableList([])
            return x + y

        assert computation() == ImmutableList([])

    def test_single_element_lists(self):
        @do(ImmutableList)
        def computation() -> DoBlock[int]:
            x: int = yield ImmutableList([5])
            y: int = yield ImmutableList([3])
            return x * y

        assert computation() == ImmutableList([15])

    def test_single_list_flatmap(self):
        @do(ImmutableList)
        def computation() -> DoBlock[int]:
            x: int = yield ImmutableList([1, 2, 3])
            sign: int = yield ImmutableList([1, -1])
            return x * sign

        assert computation() == ImmutableList([1, -1, 2, -2, 3, -3])

    def test_three_lists_cartesian(self):
        @do(ImmutableList)
        def computation() -> DoBlock[int]:
            x: int = yield ImmutableList([0, 1])
            y: int = yield ImmutableList([0, 1])
            z: int = yield ImmutableList([0, 1])
            return x + y + z

        assert computation() == ImmutableList([0, 1, 1, 2, 1, 2, 2, 3])
