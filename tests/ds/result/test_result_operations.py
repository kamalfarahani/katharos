from collections.abc import Callable
from decimal import DivisionByZero

from katharos.ds.result import Result


def divide_safe(x: float, y: float) -> Result[Exception, float]:
    if y == 0:
        return Result.Failure(DivisionByZero("Division by zero"))
    return Result.Success(x / y)


class TestResultChaining:
    def test_chaining_multiple_operations_success(self):
        def add_ten(x: int) -> int:
            return x + 10

        def mul_two_result(x: int) -> Result[Exception, int]:
            return Result.Success(x * 2)

        def sub_five(x: int) -> int:
            return x - 5

        result = Result.Success(5).fmap(add_ten).bind(mul_two_result).fmap(sub_five)

        assert result.is_success()
        assert result.value == 25

    def test_chaining_stops_at_failure(self):
        error = ValueError("computation failed")

        def add_ten(x: int) -> int:
            return x + 10

        def fail(x: int) -> Result[Exception, int]:
            return Result.Failure(error)

        def mul_two(x: int) -> int:
            return x * 2

        result = Result.Success(5).fmap(add_ten).bind(fail).fmap(mul_two)

        assert result.is_failure()
        assert result.error == error

    def test_chaining_with_applicative(self):
        def add(x: int) -> Callable[[int], int]:
            return lambda y: x + y

        result = Result.Success(10) ** (Result.Success(5) ** Result.Success(add))

        assert result.is_success()
        assert result.value == 15

    def test_complex_computation_chain(self):
        def divide_by_two(x: float) -> Result[Exception, float]:
            return divide_safe(x, 2)

        def add_ten(x: float) -> float:
            return x + 10

        def divide_by_five(x: float) -> Result[Exception, float]:
            return divide_safe(x, 5)

        result = (
            Result.Success(100).bind(divide_by_two).fmap(add_ten).bind(divide_by_five)
        )

        assert result.is_success()
        assert result.value == 12.0

    def test_complex_computation_chain_with_failure(self):
        def divide_by_two(x: float) -> Result[Exception, float]:
            return divide_safe(x, 2)

        def add_ten(x: float) -> Result[Exception, float]:
            return Result.Success(x + 10)

        def divide_by_zero(x: float) -> Result[Exception, float]:
            return divide_safe(x, 0)

        result = Result.Success(100) | divide_by_two | add_ten | divide_by_zero
        assert result.is_failure()
        assert isinstance(result.error, DivisionByZero)


class TestResultStateChecking:
    def test_check_success_state(self):
        result = Result.Success(42)

        assert result.is_success()
        assert not result.is_failure()
        assert result.value == 42

    def test_check_failure_state(self):
        error = ValueError("test error")
        result: Result[Exception, int] = Result.Failure(error)

        assert result.is_failure()
        assert not result.is_success()
        assert result.error == error
