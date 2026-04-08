from katharos.ds.result import Result


class TestResultBasics:
    def test_success_creation(self):
        result = Result.Success(42)
        assert result.is_success()
        assert not result.is_failure()
        assert result.value == 42
        assert repr(result) == "Success(42)"

    def test_failure_creation(self):
        error = ValueError("test error")
        result = Result.Failure(error)
        assert result.is_failure()
        assert not result.is_success()
        assert result.error == error
        assert repr(result) == f"Failure({error!r})"

    def test_pure(self):
        result = Result.pure(42)
        assert result.is_success()
        assert result.value == 42

    def test_pure_with_exception_raises(self):
        try:
            Result.pure(ValueError("error"))
            assert False, "Should have raised TypeError"
        except TypeError as e:
            assert "Cannot create a Result with an exception" in str(e)


class TestResultTypeTransformations:
    def test_int_to_string_transformation(self):
        result = Result.Success(42).fmap(str)

        assert result.is_success()
        assert result.value == "42"

    def test_string_to_int_transformation(self):
        result = Result.Success("42").fmap(int)

        assert result.is_success()
        assert result.value == 42

    def test_list_transformation(self):
        def double_list(xs: list[int]) -> list[int]:
            return [x * 2 for x in xs]

        result = Result.Success([1, 2, 3]).fmap(double_list)

        assert result.is_success()
        assert result.value == [2, 4, 6]

    def test_nested_result_flattening(self):
        def identity_result(x: Result[Exception, int]) -> Result[Exception, int]:
            return x

        nested = Result.Success(Result.Success(42))

        flattened = nested.bind(identity_result)

        assert flattened.is_success()
        assert flattened.value == 42
