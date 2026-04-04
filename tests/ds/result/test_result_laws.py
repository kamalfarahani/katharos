from collections.abc import Callable

from katharos.ds.result import Result
from katharos.functools import F


class TestFunctorLaws:
    """
    Functor laws:
    1. Identity: fmap(id, x) == x
    2. Composition: fmap(f . g, x) == fmap(f, fmap(g, x))
    """

    def test_functor_identity_success(self):
        result = Result(42)

        mapped = result.fmap(F.id)

        assert mapped.is_success()
        assert mapped.value == result.value

    def test_functor_identity_failure(self):
        error = ValueError("test error")
        result = Result(error)

        mapped = result.fmap(F.id)

        assert mapped.is_failure()
        assert mapped.value == error

    def test_functor_composition_success(self):
        def f(x: int) -> int:
            return x * 2

        def g(x: int) -> int:
            return x + 10

        result = Result(5)

        def composed(x: int) -> int:
            return f(g(x))

        left = result.fmap(composed)
        right = result.fmap(g).fmap(f)

        assert left.is_success()
        assert right.is_success()
        assert left.value == right.value
        assert left.value == 30

    def test_functor_composition_failure(self):
        def f(x: int) -> int:
            return x * 2

        def g(x: int) -> int:
            return x + 10

        error = ValueError("test error")
        result = Result[int, Exception](error)

        def composed(x: int) -> int:
            return f(g(x))

        left = result.fmap(composed)
        right = result.fmap(g).fmap(f)

        assert left.is_failure()
        assert right.is_failure()
        assert left.value == error
        assert right.value == error

    def test_functor_with_different_types(self):
        result = Result(42)
        mapped = result.fmap(str)

        assert mapped.is_success()
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
        value = Result(42)
        id_int: Callable[[int], int] = F.id
        s: Result[Callable[[int], int], Exception] = Result(id_int)
        result = value.ap(s)

        assert result.is_success()
        assert result.value == value.value

    def test_applicative_identity_failure(self):
        def identity(x: int) -> int:
            return x

        error = ValueError("test error")
        value = Result[int, Exception](error)

        result = value.ap(Result(identity))

        assert result.is_failure()
        assert result.value == error

    def test_applicative_homomorphism(self):
        def f(x: int) -> int:
            return x * 2

        x = 21

        left = Result(x).ap(Result(f))
        right = Result(f(x))

        assert left.is_success()
        assert right.is_success()
        assert left.value == right.value
        assert left.value == 42

    def test_applicative_interchange(self):
        def f(x: int) -> int:
            return x * 2

        y = 21

        left = Result(y).ap(Result(f))

        def apply_to_y(g: Callable[[int], int]) -> int:
            return g(y)

        right = Result(f).ap(Result(apply_to_y))

        assert left.is_success()
        assert right.is_success()
        assert left.value == right.value
        assert left.value == 42

    def test_applicative_composition(self):
        def mul_two(x: int) -> int:
            return x * 2

        def add_ten(x: int) -> int:
            return x + 10

        u: Result[Callable[[int], int], Exception] = Result(mul_two)
        v: Result[Callable[[int], int], Exception] = Result(add_ten)
        w: Result[int, Exception] = Result(5)

        left = (w**v) ** u
        right = w ** (v ** (u ** Result(F.compose)))

        assert left.is_success()
        assert right.is_success()
        assert left.value == right.value
        assert left.value == 30

    def test_applicative_failure_in_function(self):
        error = ValueError("function error")
        value = Result(42)

        result = value.ap(Result(error))

        assert result.is_failure()
        assert result.value == error

    def test_applicative_failure_in_value(self):
        def f(x: int) -> int:
            return x * 2

        error = ValueError("value error")
        value = Result[int, ValueError](error)

        result = value.ap(Result(f))

        assert result.is_failure()
        assert result.value == error

    def test_applicative_both_failures(self):
        func_error = ValueError("function error")
        value_error = ValueError("value error")

        result = Result(value_error).ap(Result(func_error))

        assert result.is_failure()
        assert result.value == value_error


class TestMonadLaws:
    """
    Monad laws:
    1. Left identity: pure(x).bind(f) == f(x)
    2. Right identity: m.bind(pure) == m
    3. Associativity: m.bind(f).bind(g) == m.bind(lambda x: f(x).bind(g))
    """

    def test_monad_left_identity_success(self):
        def f(a: int) -> Result[int, Exception]:
            return Result(a * 2)

        x = 42

        left = Result.pure(x).bind(f)
        right = f(x)

        assert left.is_success()
        assert right.is_success()
        assert left.value == right.value
        assert left.value == 84

    def test_monad_left_identity_to_failure(self):
        error = ValueError("test error")

        def f(a: int) -> Result[int, Exception]:
            return Result(error)

        x = 42

        left = Result.pure(x).bind(f)
        right = f(x)

        assert left.is_failure()
        assert right.is_failure()
        assert left.value == error
        assert right.value == error

    def test_monad_right_identity_success(self):
        m = Result(42)

        result = m.bind(Result.pure)

        assert result.is_success()
        assert result.value == m.value

    def test_monad_right_identity_failure(self):
        error = ValueError("test error")
        m = Result(error)

        result = m.bind(Result.pure)

        assert result.is_failure()
        assert result.value == error

    def test_monad_associativity_success(self):
        def f(x: int) -> Result[int, Exception]:
            return Result(x + 10)

        def g(x: int) -> Result[int, Exception]:
            return Result(x * 2)

        m = Result(5)

        def bind_f_then_g(x: int) -> Result[int, Exception]:
            return f(x).bind(g)

        left = m.bind(f).bind(g)
        right = m.bind(bind_f_then_g)

        assert left.is_success()
        assert right.is_success()
        assert left.value == right.value
        assert left.value == 30

    def test_monad_associativity_failure_in_first(self):
        def f(x: int) -> Result[int, Exception]:
            return Result(x + 10)

        def g(x: int) -> Result[int, Exception]:
            return Result(x * 2)

        error = ValueError("first error")
        m = Result[int, Exception](error)

        def bind_f_then_g(x: int) -> Result[int, Exception]:
            return f(x).bind(g)

        left = m.bind(f).bind(g)
        right = m.bind(bind_f_then_g)

        assert left.is_failure()
        assert right.is_failure()
        assert left.value == error
        assert right.value == error

    def test_monad_associativity_failure_in_f(self):
        error = ValueError("f error")

        def f(x: int) -> Result[int, Exception]:
            return Result(error)

        def g(x: int) -> Result[int, Exception]:
            return Result(x * 2)

        m = Result(5)

        def bind_f_then_g(x: int) -> Result[int, Exception]:
            return f(x).bind(g)

        left = m.bind(f).bind(g)
        right = m.bind(bind_f_then_g)

        assert left.is_failure()
        assert right.is_failure()
        assert left.value == error
        assert right.value == error

    def test_monad_associativity_failure_in_g(self):
        error = ValueError("g error")

        def f(x: int) -> Result[int, Exception]:
            return Result(x + 10)

        def g(x: int) -> Result[int, Exception]:
            return Result(error)

        m = Result(5)

        def bind_f_then_g(x: int) -> Result[int, Exception]:
            return f(x).bind(g)

        left = m.bind(f).bind(g)
        right = m.bind(bind_f_then_g)

        assert left.is_failure()
        assert right.is_failure()
        assert left.value == error
        assert right.value == error
