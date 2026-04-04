from collections.abc import Callable
from decimal import DivisionByZero

from katharos.ds.result import Result


def divide_safe(x: float, y: float) -> Result[float, Exception]:
    if y == 0:
        return Result(DivisionByZero("Division by zero"))
    return Result(x / y)


class TestResultChaining:
    def test_chaining_multiple_operations_success(self):
        def add_ten(x: int) -> int:
            return x + 10

        def mul_two_result(x: int) -> Result[int, Exception]:
            return Result(x * 2)

        def sub_five(x: int) -> int:
            return x - 5

        result = Result(5).fmap(add_ten).bind(mul_two_result).fmap(sub_five)

        assert result.is_success()
        assert result.value == 25

    def test_chaining_stops_at_failure(self):
        error = ValueError("computation failed")

        def add_ten(x: int) -> int:
            return x + 10

        def fail(x: int) -> Result[int, Exception]:
            return Result[int, Exception](error)

        def mul_two(x: int) -> int:
            return x * 2

        result = Result(5).fmap(add_ten).bind(fail).fmap(mul_two)

        assert result.is_failure()
        assert result.value == error

    def test_chaining_with_applicative(self):
        def add(x: int) -> Callable[[int], int]:
            return lambda y: x + y

        result = Result(10) ** (Result(5) ** Result(add))

        assert result.is_success()
        assert result.value == 15

    def test_complex_computation_chain(self):
        def divide_by_two(x: float) -> Result[float, Exception]:
            return divide_safe(x, 2)

        def add_ten(x: float) -> float:
            return x + 10

        def divide_by_five(x: float) -> Result[float, Exception]:
            return divide_safe(x, 5)

        result = Result(100).bind(divide_by_two).fmap(add_ten).bind(divide_by_five)

        assert result.is_success()
        assert result.value == 12.0

    def test_complex_computation_chain_with_failure(self):
        def divide_by_two(x: float) -> Result[float, Exception]:
            return divide_safe(x, 2)

        def add_ten(x: float) -> Result[float, Exception]:
            return Result(x + 10)

        def divide_by_zero(x: float) -> Result[float, Exception]:
            return divide_safe(x, 0)

        result = Result(100) | divide_by_two | add_ten | divide_by_zero
        assert result.is_failure()
        assert isinstance(result.value, DivisionByZero)


class TestResultStateChecking:
    def test_check_success_state(self):
        result = Result(42)

        assert result.is_success()
        assert not result.is_failure()
        assert result.value == 42

    def test_check_failure_state(self):
        error = ValueError("test error")
        result = Result[int, Exception](error)

        assert result.is_failure()
        assert not result.is_success()
        assert result.value == error
