from collections.abc import Callable
from decimal import DivisionByZero

import pytest

from katharos.ds.result import Failure, Result, Success


def divide_safe(x: float, y: float) -> Result[float]:
    if y == 0:
        return Failure(DivisionByZero("Division by zero"))
    return Success(x / y)


class TestResultChaining:
    def test_chaining_multiple_operations_success(self):
        def add_ten(x: int) -> int:
            return x + 10

        def mul_two_result(x: int) -> Result[int]:
            return Success(x * 2)

        def sub_five(x: int) -> int:
            return x - 5

        result = Success(5).fmap(add_ten).bind(mul_two_result).fmap(sub_five)

        assert isinstance(result, Success)
        assert result.value == 25

    def test_chaining_stops_at_failure(self):
        error = ValueError("computation failed")

        def add_ten(x: int) -> int:
            return x + 10

        def fail(x: int) -> Result[int]:
            return Failure[int](error)

        def mul_two(x: int) -> int:
            return x * 2

        result = Success(5).fmap(add_ten).bind(fail).fmap(mul_two)

        assert isinstance(result, Failure)
        assert result.error == error

    def test_chaining_with_applicative(self):
        def add(x: int) -> Callable[[int], int]:
            return lambda y: x + y

        result = Success(10) ^ (Success(5) ^ Success(add))

        assert isinstance(result, Success)
        assert result.value == 15

    def test_complex_computation_chain(self):
        def divide_by_two(x: float) -> Result[float]:
            return divide_safe(x, 2)

        def add_ten(x: float) -> float:
            return x + 10

        def divide_by_five(x: float) -> Result[float]:
            return divide_safe(x, 5)

        result = Success(100).bind(divide_by_two).fmap(add_ten).bind(divide_by_five)

        assert isinstance(result, Success)
        assert result.value == 12.0

    def test_complex_computation_chain_with_failure(self):
        def divide_by_two(x: float) -> Result[float]:
            return divide_safe(x, 2)

        def add_ten(x: float) -> Result[float]:
            return Success(x + 10)

        def divide_by_zero(x: float) -> Result[float]:
            return divide_safe(x, 0)

        result = Success(100) | divide_by_two | add_ten | divide_by_zero
        assert isinstance(result, Failure)
        assert isinstance(result.error, ZeroDivisionError)


class TestResultPatternMatching:
    def test_match_success(self):
        result = Success(42)

        match result:
            case Success(value=v):
                assert v == 42
            case Failure(error=_):
                pytest.fail("Should not match Failure")

    def test_match_failure(self):
        error = ValueError("test error")
        result = Failure[int](error)

        match result:
            case Success(value=_):
                pytest.fail("Should not match Success")
            case Failure(error=e):
                assert e == error
