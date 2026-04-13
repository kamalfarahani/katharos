from typing import cast

import pytest

from katharos.ds import ImmutableList, Maybe, Result
from katharos.syntax_sugar import Do
from katharos.syntax_sugar.do import DoVariable


class TestDoWithMaybe:
    def test_two_just_values_are_combined(self):
        with Do() as do:
            x = do.arrow(Maybe.Just(3))
            y = do.arrow(Maybe.Just(4))
            result = do.eval(lambda x, y: Maybe.Just(x + y), x=x, y=y)
        assert result == Maybe.Just(7)

    def test_first_nothing_short_circuits(self):
        with Do() as do:
            x = do.arrow(Maybe.Nothing())
            y = do.arrow(Maybe.Just(4))
            result = do.eval(lambda x, y: Maybe.Just(x + y), x=x, y=y)
        assert result == Maybe.Nothing()

    def test_second_nothing_short_circuits(self):
        with Do() as do:
            x = do.arrow(Maybe.Just(3))
            y = do.arrow(Maybe.Nothing())
            result = do.eval(lambda x, y: Maybe.Just(x + y), x=x, y=y)
        assert result == Maybe.Nothing()

    def test_single_just_value(self):
        with Do() as do:
            x = do.arrow(Maybe.Just(10))
            result = do.eval(lambda x: Maybe.Just(x * 2), x=x)
        assert result == Maybe.Just(20)

    def test_single_nothing(self):
        with Do() as do:
            x = do.arrow(Maybe.Nothing())
            result = do.eval(lambda x: Maybe.Just(x * 2), x=x)
        assert result == Maybe.Nothing()

    def test_three_just_values(self):
        with Do() as do:
            x = do.arrow(Maybe.Just(1))
            y = do.arrow(Maybe.Just(2))
            z = do.arrow(Maybe.Just(3))
            result = do.eval(lambda x, y, z: Maybe.Just(x + y + z), x=x, y=y, z=z)
        assert result == Maybe.Just(6)

    def test_middle_nothing_short_circuits(self):
        with Do() as do:
            x = do.arrow(Maybe.Just(1))
            y = do.arrow(Maybe.Nothing())
            z = do.arrow(Maybe.Just(3))
            result = do.eval(lambda x, y, z: Maybe.Just(x + y + z), x=x, y=y, z=z)
        assert result == Maybe.Nothing()

    def test_f_returning_nothing_propagates(self):
        with Do() as do:
            x = do.arrow(Maybe.Just(0))
            result = do.eval(
                lambda x: Maybe.Nothing() if x == 0 else Maybe.Just(10 // x),
                x=x,
            )
        assert result == Maybe.Nothing()

    def test_vars_cleared_after_context_exit(self):
        do = Do()
        with do:
            x = do.arrow(Maybe.Just(1))
            do.eval(lambda x: Maybe.Just(x), x=x)
        assert do._vars == []


class TestDoWithResult:
    def test_two_successes_are_combined(self):
        with Do() as do:
            x = do.arrow(Result.Success(10))
            y = do.arrow(Result.Success(5))
            result = do.eval(lambda x, y: Result.Success(x - y), x=x, y=y)
        assert result == Result.Success(5)

    def test_first_failure_short_circuits(self):
        err = ValueError("bad input")
        with Do() as do:
            x = do.arrow(Result.Failure(err))
            y = do.arrow(Result.Success(5))
            result = cast(Result, do.eval(lambda x, y: Result.Success(x + y), x=x, y=y))
        assert result.is_failure()
        assert result.error is err

    def test_second_failure_short_circuits(self):
        err = TypeError("wrong type")
        with Do() as do:
            x = do.arrow(Result.Success(10))
            y = do.arrow(Result.Failure(err))
            result = cast(Result, do.eval(lambda x, y: Result.Success(x + y), x=x, y=y))
        assert result.is_failure()
        assert result.error is err

    def test_single_success(self):
        with Do() as do:
            x = do.arrow(Result.Success(7))
            result = do.eval(lambda x: Result.Success(x**2), x=x)
        assert result == Result.Success(49)

    def test_single_failure(self):
        err = RuntimeError("oops")
        with Do() as do:
            x = do.arrow(Result.Failure(err))
            result = cast(Result, do.eval(lambda x: Result.Success(x + 1), x=x))
        assert result.is_failure()
        assert result.error is err

    def test_three_successes(self):
        with Do() as do:
            x = do.arrow(Result.Success(2))
            y = do.arrow(Result.Success(3))
            z = do.arrow(Result.Success(4))
            result = do.eval(lambda x, y, z: Result.Success(x * y * z), x=x, y=y, z=z)
        assert result == Result.Success(24)

    def test_f_returning_failure_propagates(self):
        err = ZeroDivisionError("division by zero")
        with Do() as do:
            x = do.arrow(Result.Success(0))
            result = cast(
                Result,
                do.eval(
                    lambda x: (
                        Result.Failure(err) if x == 0 else Result.Success(10 // x)
                    ),
                    x=x,
                ),
            )
        assert result.is_failure()
        assert result.error is err


class TestDoWithImmutableList:
    def test_cartesian_product_of_two_lists(self):
        with Do() as do:
            x = do.arrow(ImmutableList([1, 2]))
            y = do.arrow(ImmutableList([10, 20]))
            result = do.eval(lambda x, y: ImmutableList([x + y]), x=x, y=y)
        assert result == ImmutableList([11, 21, 12, 22])

    def test_empty_first_list_yields_empty(self):
        with Do() as do:
            x = do.arrow(ImmutableList([]))
            y = do.arrow(ImmutableList([1, 2, 3]))
            result = do.eval(lambda x, y: ImmutableList([x + y]), x=x, y=y)
        assert result == ImmutableList([])

    def test_empty_second_list_yields_empty(self):
        with Do() as do:
            x = do.arrow(ImmutableList([1, 2, 3]))
            y = do.arrow(ImmutableList([]))
            result = do.eval(lambda x, y: ImmutableList([x + y]), x=x, y=y)
        assert result == ImmutableList([])

    def test_single_element_lists(self):
        with Do() as do:
            x = do.arrow(ImmutableList([5]))
            y = do.arrow(ImmutableList([3]))
            result = do.eval(lambda x, y: ImmutableList([x * y]), x=x, y=y)
        assert result == ImmutableList([15])

    def test_single_list_flatmap(self):
        with Do() as do:
            x = do.arrow(ImmutableList([1, 2, 3]))
            result = do.eval(lambda x: ImmutableList([x, -x]), x=x)
        assert result == ImmutableList([1, -1, 2, -2, 3, -3])

    def test_three_lists_cartesian(self):
        with Do() as do:
            x = do.arrow(ImmutableList([0, 1]))
            y = do.arrow(ImmutableList([0, 1]))
            z = do.arrow(ImmutableList([0, 1]))
            result = do.eval(lambda x, y, z: ImmutableList([x + y + z]), x=x, y=y, z=z)
        assert result == ImmutableList([0, 1, 1, 2, 1, 2, 2, 3])


class TestDoErrors:
    def test_variable_not_registered_raises(self):
        with pytest.raises(ValueError):
            with Do() as do:
                external_var = DoVariable(index=0, monad=Maybe.Just(1))
                do.eval(lambda x: Maybe.Just(x), x=external_var)

    def test_variable_from_different_do_block_raises(self):
        with pytest.raises(ValueError):
            with Do() as do1:
                x = do1.arrow(Maybe.Just(1))

            with Do() as do2:
                do2.eval(lambda x: Maybe.Just(x), x=x)
