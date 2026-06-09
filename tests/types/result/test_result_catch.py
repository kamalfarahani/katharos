import pytest

from katharos.types.result import Result


class TestCatchSuccess:
    def test_no_exception_returns_success(self):
        @Result.catch(ValueError)
        def parse(s: str) -> int:
            return int(s)

        result = parse("42")
        assert result.is_success()
        assert result.value == 42

    def test_success_wraps_return_value(self):
        @Result.catch(RuntimeError)
        def greet(name: str) -> str:
            return f"hello {name}"

        result = greet("world")
        assert result.is_success()
        assert result.value == "hello world"

    def test_multiple_positional_args(self):
        @Result.catch(ZeroDivisionError)
        def divide(a: float, b: float) -> float:
            return a / b

        result = divide(10.0, 2.0)
        assert result.is_success()
        assert result.value == 5.0

    def test_keyword_args(self):
        @Result.catch(ValueError)
        def repeat(s: str, *, times: int) -> str:
            return s * times

        result = repeat("ab", times=3)
        assert result.is_success()
        assert result.value == "ababab"

    def test_mixed_positional_and_keyword_args(self):
        @Result.catch(TypeError)
        def add(x: int, y: int, z: int = 0) -> int:
            return x + y + z

        result = add(1, 2, z=3)
        assert result.is_success()
        assert result.value == 6

    def test_returns_none(self):
        @Result.catch(OSError)
        def do_nothing() -> None:
            pass

        result = do_nothing()
        assert result.is_success()
        assert result.value is None

    def test_returns_complex_type(self):
        @Result.catch(ValueError)
        def build_dict(keys: list[str]) -> dict[str, int]:
            return {k: len(k) for k in keys}

        result = build_dict(["a", "bb", "ccc"])
        assert result.is_success()
        assert result.value == {"a": 1, "bb": 2, "ccc": 3}


class TestCatchFailure:
    def test_caught_exception_returns_failure(self):
        @Result.catch(ValueError)
        def parse(s: str) -> int:
            return int(s)

        result = parse("not-a-number")
        assert result.is_failure()
        assert isinstance(result.error, ValueError)

    def test_failure_preserves_exception_instance(self):
        error = ValueError("specific message")

        @Result.catch(ValueError)
        def boom() -> int:
            raise error

        result = boom()
        assert result.is_failure()
        assert result.error is error

    def test_failure_preserves_exception_message(self):
        @Result.catch(RuntimeError)
        def fail() -> str:
            raise RuntimeError("something went wrong")

        result = fail()
        assert result.is_failure()
        assert str(result.error) == "something went wrong"

    def test_catches_subclass_of_declared_exception(self):
        @Result.catch(OSError)
        def open_file(path: str) -> str:
            raise FileNotFoundError(f"{path} not found")

        result = open_file("/nonexistent")
        assert result.is_failure()
        assert isinstance(result.error, FileNotFoundError)

    def test_zero_division(self):
        @Result.catch(ZeroDivisionError)
        def divide(a: float, b: float) -> float:
            return a / b

        result = divide(1.0, 0.0)
        assert result.is_failure()
        assert isinstance(result.error, ZeroDivisionError)


class TestCatchPropagation:
    def test_uncaught_exception_propagates(self):
        @Result.catch(ValueError)
        def boom() -> int:
            raise TypeError("wrong type")

        with pytest.raises(TypeError, match="wrong type"):
            boom()

    def test_only_declared_type_is_caught(self):
        @Result.catch(ValueError)
        def maybe_fails(exc_type: type[Exception]) -> int:
            raise exc_type("error")

        assert maybe_fails(ValueError).is_failure()

        with pytest.raises(RuntimeError):
            maybe_fails(RuntimeError)

    def test_parent_exception_does_not_catch_sibling(self):
        @Result.catch(FileNotFoundError)
        def fail() -> None:
            raise PermissionError("denied")

        with pytest.raises(PermissionError):
            fail()


class TestCatchComposition:
    def test_result_of_catch_can_be_fmapped(self):
        @Result.catch(ValueError)
        def parse(s: str) -> int:
            return int(s)

        result = parse("10").fmap(lambda x: x * 2)
        assert result.is_success()
        assert result.value == 20

    def test_fmap_skipped_on_failure(self):
        @Result.catch(ValueError)
        def parse(s: str) -> int:
            return int(s)

        called = False

        def side_effect(x: int) -> int:
            nonlocal called
            called = True
            return x

        parse("bad").fmap(side_effect)
        assert not called

    def test_chained_with_bind(self):
        @Result.catch(Exception)
        def parse(s: str) -> int:
            return int(s)

        @Result.catch(Exception)
        def invert(x: int) -> float:
            return 1 / x

        result = parse("4") | (lambda x: invert(x))
        assert result.is_success()
        assert result.value == 0.25

    def test_bind_short_circuits_on_failure(self):
        @Result.catch(Exception)
        def parse(s: str) -> int:
            return int(s)

        @Result.catch(Exception)
        def invert(x: int) -> float:
            return 1 / x

        result = parse("bad") | (lambda x: invert(x))
        assert result.is_failure()
        assert isinstance(result.error, ValueError)

    def test_decorator_applied_multiple_times_independently(self):
        @Result.catch(ValueError)
        def parse(s: str) -> int:
            return int(s)

        assert parse("1").is_success()
        assert parse("bad").is_failure()
        assert parse("2").is_success()

    def test_two_decorated_functions_are_independent(self):
        @Result.catch(ValueError)
        def parse_int(s: str) -> int:
            return int(s)

        @Result.catch(KeyError)
        def lookup(d: dict[str, int], key: str) -> int:
            return d[key]

        assert parse_int("5").is_success()
        assert parse_int("x").is_failure()
        assert lookup({"a": 1}, "a").is_success()
        assert lookup({"a": 1}, "b").is_failure()


class TestCatchMetadata:
    def test_preserves_function_name(self):
        @Result.catch(ValueError)
        def my_function() -> int:
            return 1

        assert my_function.__name__ == "my_function"

    def test_preserves_function_docstring(self):
        @Result.catch(ValueError)
        def documented() -> int:
            """This is the docstring."""
            return 1

        assert documented.__doc__ == "This is the docstring."
