from collections.abc import Callable

from katharos.ds.result import Failure, Result, Success
from katharos.functools import F


class TestFunctorLaws:
    """
    Functor laws:
    1. Identity: fmap(id, x) == x
    2. Composition: fmap(f . g, x) == fmap(f, fmap(g, x))
    """

    def test_functor_identity_success(self):
        result = Success(42)

        mapped = result.fmap(F.id)

        assert isinstance(mapped, Success)
        assert mapped.value == result.value

    def test_functor_identity_failure(self):
        error = ValueError("test error")
        result = Failure[int, Exception](error)

        mapped = result.fmap(F.id)

        assert isinstance(mapped, Failure)
        assert mapped.error == error

    def test_functor_composition_success(self):
        def f(x: int) -> int:
            return x * 2

        def g(x: int) -> int:
            return x + 10

        result = Success(5)

        def composed(x: int) -> int:
            return f(g(x))

        left = result.fmap(composed)
        right = result.fmap(g).fmap(f)

        assert isinstance(left, Success)
        assert isinstance(right, Success)
        assert left.value == right.value
        assert left.value == 30

    def test_functor_composition_failure(self):
        def f(x: int) -> int:
            return x * 2

        def g(x: int) -> int:
            return x + 10

        error = ValueError("test error")
        result = Failure[int, Exception](error)

        def composed(x: int) -> int:
            return f(g(x))

        left = result.fmap(composed)
        right = result.fmap(g).fmap(f)

        assert isinstance(left, Failure)
        assert isinstance(right, Failure)
        assert left.error == error
        assert right.error == error

    def test_functor_with_different_types(self):
        result = Success(42)
        mapped = result.fmap(str)

        assert isinstance(mapped, Success)
        assert mapped.value == "42"
        assert isinstance(mapped.value, str)


class TestApplicativeLaws:
    """
    Applicative laws:
    1. Identity: pure(id) <*> v == v
    2. Composition: pure(.) <*> u <*> v <*> w == u <*> (v <*> w)
    3. Homomorphism: pure(f) <*> pure(x) == pure(f(x))
    4. Interchange: u <*> pure(y) == pure(lambda f: f(y)) <*> u
    """

    def test_applicative_identity_success(self):
        value = Success(42)
        id_int: Callable[[int], int] = F.id
        s: Result[Callable[[int], int], Exception] = Success(id_int)
        result = value.ap(s)

        assert isinstance(result, Success)
        assert result.value == value.value

    def test_applicative_identity_failure(self):
        def identity(x: int) -> int:
            return x

        error = ValueError("test error")
        value = Failure[int, Exception](error)

        result = value.ap(Success(identity))

        assert isinstance(result, Failure)
        assert result.error == error

    def test_applicative_homomorphism(self):
        def f(x: int) -> int:
            return x * 2

        x = 21

        left = Success(x).ap(Success(f))
        right = Success(f(x))

        assert isinstance(left, Success)
        assert isinstance(right, Success)
        assert left.value == right.value
        assert left.value == 42

    def test_applicative_interchange(self):
        def f(x: int) -> int:
            return x * 2

        y = 21

        left = Success(y).ap(Success(f))

        def apply_to_y(g: Callable[[int], int]) -> int:
            return g(y)

        right = Success(f).ap(Success(apply_to_y))

        assert isinstance(left, Success)
        assert isinstance(right, Success)
        assert left.value == right.value
        assert left.value == 42

    def test_applicative_composition(self):
        def mul_two(x: int) -> int:
            return x * 2

        def add_ten(x: int) -> int:
            return x + 10

        u: Result[Callable[[int], int], Exception] = Success(mul_two)
        v: Result[Callable[[int], int], Exception] = Success(add_ten)
        w: Result[int, Exception] = Success(5)

        left = (w**v) ** u
        right = w ** (v ** (u ** Success(F.compose)))

        assert isinstance(left, Success)
        assert isinstance(right, Success)
        assert left.value == right.value
        assert left.value == 30

    def test_applicative_failure_in_function(self):
        error = ValueError("function error")
        value = Success(42)

        result = value.ap(Failure(error))

        assert isinstance(result, Failure)
        assert result.error == error

    def test_applicative_failure_in_value(self):
        def f(x: int) -> int:
            return x * 2

        error = ValueError("value error")
        value = Failure[int, Exception](error)

        result = value.ap(Success(f))

        assert isinstance(result, Failure)
        assert result.error == error

    def test_applicative_both_failures(self):
        func_error = ValueError("function error")
        value_error = ValueError("value error")

        result = Failure[int, Exception](value_error).ap(Failure(func_error))

        assert isinstance(result, Failure)
        assert result.error == value_error


class TestMonadLaws:
    """
    Monad laws:
    1. Left identity: pure(x).bind(f) == f(x)
    2. Right identity: m.bind(pure) == m
    3. Associativity: m.bind(f).bind(g) == m.bind(lambda x: f(x).bind(g))
    """

    def test_monad_left_identity_success(self):
        def f(a: int) -> Result[int, Exception]:
            return Success(a * 2)

        x = 42

        left = Result.pure(x).bind(f)
        right = f(x)

        assert isinstance(left, Success)
        assert isinstance(right, Success)
        assert left.value == right.value
        assert left.value == 84

    def test_monad_left_identity_to_failure(self):
        error = ValueError("test error")

        def f(a: int) -> Result[int, Exception]:
            return Failure[int, Exception](error)

        x = 42

        left = Result.pure(x).bind(f)
        right = f(x)

        assert isinstance(left, Failure)
        assert isinstance(right, Failure)
        assert left.error == error
        assert right.error == error

    def test_monad_right_identity_success(self):
        m = Success(42)

        result = m.bind(Result.pure)

        assert isinstance(result, Success)
        assert result.value == m.value

    def test_monad_right_identity_failure(self):
        error = ValueError("test error")
        m = Failure[int, Exception](error)

        result = m.bind(Result.pure)

        assert isinstance(result, Failure)
        assert result.error == error

    def test_monad_associativity_success(self):
        def f(x: int) -> Result[int, Exception]:
            return Success(x + 10)

        def g(x: int) -> Result[int, Exception]:
            return Success(x * 2)

        m = Success(5)

        def bind_f_then_g(x: int) -> Result[int, Exception]:
            return f(x).bind(g)

        left = m.bind(f).bind(g)
        right = m.bind(bind_f_then_g)

        assert isinstance(left, Success)
        assert isinstance(right, Success)
        assert left.value == right.value
        assert left.value == 30

    def test_monad_associativity_failure_in_first(self):
        def f(x: int) -> Result[int, Exception]:
            return Success(x + 10)

        def g(x: int) -> Result[int, Exception]:
            return Success(x * 2)

        error = ValueError("first error")
        m = Failure[int, Exception](error)

        def bind_f_then_g(x: int) -> Result[int, Exception]:
            return f(x).bind(g)

        left = m.bind(f).bind(g)
        right = m.bind(bind_f_then_g)

        assert isinstance(left, Failure)
        assert isinstance(right, Failure)
        assert left.error == error
        assert right.error == error

    def test_monad_associativity_failure_in_f(self):
        error = ValueError("f error")

        def f(x: int) -> Result[int, Exception]:
            return Failure[int, Exception](error)

        def g(x: int) -> Result[int, Exception]:
            return Success(x * 2)

        m = Success(5)

        def bind_f_then_g(x: int) -> Result[int, Exception]:
            return f(x).bind(g)

        left = m.bind(f).bind(g)
        right = m.bind(bind_f_then_g)

        assert isinstance(left, Failure)
        assert isinstance(right, Failure)
        assert left.error == error
        assert right.error == error

    def test_monad_associativity_failure_in_g(self):
        error = ValueError("g error")

        def f(x: int) -> Result[int, Exception]:
            return Success(x + 10)

        def g(x: int) -> Result[int, Exception]:
            return Failure[int, Exception](error)

        m = Success(5)

        def bind_f_then_g(x: int) -> Result[int, Exception]:
            return f(x).bind(g)

        left = m.bind(f).bind(g)
        right = m.bind(bind_f_then_g)

        assert isinstance(left, Failure)
        assert isinstance(right, Failure)
        assert left.error == error
        assert right.error == error
