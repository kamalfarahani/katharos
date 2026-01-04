from collections.abc import Callable

from katharos.ds.side_effect import IO
from katharos.functools import F


class TestFunctorLaws:
    """
    Functor laws:
    1. Identity: fmap(id, x) == x
    2. Composition: fmap(f . g, x) == fmap(f, fmap(g, x))
    """

    def test_functor_identity(self):
        io = IO(42)

        mapped = io.fmap(F.id)

        assert isinstance(mapped, IO)
        assert mapped.value == io.value

    def test_functor_composition(self):
        def f(x: int) -> int:
            return x * 2

        def g(x: int) -> int:
            return x + 10

        io = IO(5)

        def composed(x: int) -> int:
            return f(g(x))

        left = io.fmap(composed)
        right = io.fmap(g).fmap(f)

        assert isinstance(left, IO)
        assert isinstance(right, IO)
        assert left.value == right.value
        assert left.value == 30

    def test_functor_with_different_types(self):
        io = IO(42)
        mapped = io.fmap(str)

        assert isinstance(mapped, IO)
        assert mapped.value == "42"
        assert isinstance(mapped.value, str)

    def test_functor_preserves_side_effects(self):
        io = IO(42)
        mapped = io.fmap(lambda x: x * 2)

        assert isinstance(mapped, IO)
        assert mapped.value == 84


class TestApplicativeLaws:
    """
    Applicative laws:
    1. Identity: pure(id) <*> v == v
    2. Composition: pure(.) <*> u <*> v <*> w == u <*> (v <*> w)
    3. Homomorphism: pure(f) <*> pure(x) == pure(f(x))
    4. Interchange: u <*> pure(y) == pure(lambda f: f(y)) <*> u
    """

    def test_applicative_identity(self):
        value = IO(42)
        id_int: Callable[[int], int] = F.id
        io_func: IO[Callable[[int], int]] = IO(id_int)
        result = value.ap(io_func)

        assert isinstance(result, IO)
        assert result.value == value.value

    def test_applicative_homomorphism(self):
        def f(x: int) -> int:
            return x * 2

        x = 21

        left = IO(x).ap(IO(f))
        right = IO(f(x))

        assert isinstance(left, IO)
        assert isinstance(right, IO)
        assert left.value == right.value
        assert left.value == 42

    def test_applicative_interchange(self):
        def f(x: int) -> int:
            return x * 2

        y = 21

        left = IO(y).ap(IO(f))

        def apply_to_y(g: Callable[[int], int]) -> int:
            return g(y)

        right = IO(f).ap(IO(apply_to_y))

        assert isinstance(left, IO)
        assert isinstance(right, IO)
        assert left.value == right.value
        assert left.value == 42

    def test_applicative_composition(self):
        def mul_two(x: int) -> int:
            return x * 2

        def add_ten(x: int) -> int:
            return x + 10

        u: IO[Callable[[int], int]] = IO(mul_two)
        v: IO[Callable[[int], int]] = IO(add_ten)
        w: IO[int] = IO(5)

        left = (w**v) ** u
        right = w**v**u ** IO.pure(F.compose)

        assert isinstance(left, IO)
        assert isinstance(right, IO)
        assert left.value == right.value
        assert left.value == 30

    def test_applicative_with_no_op(self):
        def f(x: int) -> int:
            return x * 2

        value = IO(21)
        func_io = IO(f)

        result = value.ap(func_io)

        assert isinstance(result, IO)
        assert result.value == 42


class TestMonadLaws:
    """
    Monad laws:
    1. Left identity: pure(x).bind(f) == f(x)
    2. Right identity: m.bind(pure) == m
    3. Associativity: m.bind(f).bind(g) == m.bind(lambda x: f(x).bind(g))
    """

    def test_monad_left_identity(self):
        def f(a: int) -> IO[int]:
            return IO(a * 2)

        x = 42

        left = IO[int].pure(x).bind(f)
        right = f(x)

        assert isinstance(left, IO)
        assert isinstance(right, IO)
        assert left.value == right.value
        assert left.value == 84

    def test_monad_right_identity(self):
        m = IO(42)

        result = m.bind(IO.pure)

        assert isinstance(result, IO)
        assert result.value == m.value

    def test_monad_associativity(self):
        def f(x: int) -> IO[int]:
            return IO(x + 10)

        def g(x: int) -> IO[int]:
            return IO(x * 2)

        m = IO(5)

        def bind_f_then_g(x: int) -> IO[int]:
            return f(x).bind(g)

        left = m.bind(f).bind(g)
        right = m.bind(bind_f_then_g)

        assert isinstance(left, IO)
        assert isinstance(right, IO)
        assert left.value == right.value
        assert left.value == 30

    def test_monad_bind_with_no_op(self):
        def f(x: int) -> IO[int]:
            return IO(x * 2)

        m = IO(21)
        result = m.bind(f)

        assert isinstance(result, IO)
        assert result.value == 42

    def test_monad_bind_chain(self):
        def add_ten(x: int) -> IO[int]:
            return IO(x + 10)

        def mul_two(x: int) -> IO[int]:
            return IO(x * 2)

        def sub_five(x: int) -> IO[int]:
            return IO(x - 5)

        result = IO(5).bind(add_ten).bind(mul_two).bind(sub_five)

        assert isinstance(result, IO)
        assert result.value == 25


class TestIOOperators:
    """
    Test IO infix operators for applicative and monad operations.
    """

    def test_xor_operator_applicative(self):
        def f(x: int) -> int:
            return x * 2

        value = IO(21)
        func_io = IO(f)

        result = value**func_io

        assert isinstance(result, IO)
        assert result.value == 42

    def test_or_operator_monad(self):
        def f(x: int) -> IO[int]:
            return IO(x * 2)

        m = IO(21)
        result = m | f

        assert isinstance(result, IO)
        assert result.value == 42

    def test_chained_or_operator(self):
        def add_ten(x: int) -> IO[int]:
            return IO(x + 10)

        def mul_two(x: int) -> IO[int]:
            return IO(x * 2)

        result = IO(5) | add_ten | mul_two

        assert isinstance(result, IO)
        assert result.value == 30


class TestIOExecution:
    """
    Test IO execution with no_op functions.
    """

    def test_execute_with_no_op(self):
        io = IO(42)
        io.execute()

        assert io.value == 42

    def test_execute_default_no_op(self):
        io = IO(42)
        io.execute()

        assert io.value == 42

    def test_execute_after_fmap(self):
        io = IO(21)
        mapped = io.fmap(lambda x: x * 2)

        mapped.execute()

        assert mapped.value == 42

    def test_execute_after_bind(self):
        def f(x: int) -> IO[int]:
            return IO(x * 2)

        io = IO(21)
        bound = io.bind(f)

        bound.execute()

        assert bound.value == 42


class TestIOPure:
    """
    Test IO pure method for creating IO instances.
    """

    def test_pure_creates_io(self):
        io = IO[int].pure(42)

        assert isinstance(io, IO)
        assert io.value == 42

    def test_pure_with_different_types(self):
        io_str = IO.pure("hello")
        io_list = IO.pure([1, 2, 3])
        io_dict = IO.pure({"key": "value"})

        assert isinstance(io_str, IO)
        assert io_str.value == "hello"

        assert isinstance(io_list, IO)
        assert io_list.value == [1, 2, 3]

        assert isinstance(io_dict, IO)
        assert io_dict.value == {"key": "value"}
