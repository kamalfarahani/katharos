from katharos.ds.result import Failure, Result, Success


class TestResultBasics:
    def test_success_creation(self):
        result = Success(42)
        assert result.value == 42
        assert repr(result) == "Success(42)"

    def test_failure_creation(self):
        error = ValueError("test error")
        result = Failure(error)
        assert result.error == error
        assert repr(result) == f"Failure({error!r})"

    def test_pure(self):
        result = Result.pure(42)
        assert isinstance(result, Success)
        assert result.value == 42


class TestResultTypeTransformations:
    def test_int_to_string_transformation(self):
        result = Success(42).fmap(str)

        assert isinstance(result, Success)
        assert result.value == "42"

    def test_string_to_int_transformation(self):
        result = Success("42").fmap(int)

        assert isinstance(result, Success)
        assert result.value == 42

    def test_list_transformation(self):
        def double_list(xs: list[int]) -> list[int]:
            return [x * 2 for x in xs]

        result = Success([1, 2, 3]).fmap(double_list)

        assert isinstance(result, Success)
        assert result.value == [2, 4, 6]

    def test_nested_result_flattening(self):
        def identity_result(x: Result[int]) -> Result[int]:
            return x

        nested = Success(Success(42))

        flattened = nested.bind(identity_result)

        assert isinstance(flattened, Success)
        assert flattened.value == 42
