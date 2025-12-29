from collections.abc import Callable

from katharos.ds.list.non_empty_list import NonEmptyList
from katharos.functools import F


class TestFunctorLaws:
    """
    Functor laws:
    1. Identity: fmap(id, x) == x
    2. Composition: fmap(f . g, x) == fmap(f, fmap(g, x))
    """

    def test_functor_identity(self):
        nel = NonEmptyList(1, [2, 3, 4])

        mapped = nel.fmap(F.id)

        assert mapped == nel
        assert list(mapped) == [1, 2, 3, 4]

    def test_functor_identity_single_element(self):
        nel = NonEmptyList(42, [])

        mapped = nel.fmap(F.id)

        assert mapped == nel
        assert list(mapped) == [42]

    def test_functor_composition(self):
        def f(x: int) -> int:
            return x * 2

        def g(x: int) -> int:
            return x + 10

        nel = NonEmptyList(5, [10, 15])

        def composed(x: int) -> int:
            return f(g(x))

        left = nel.fmap(composed)
        right = nel.fmap(g).fmap(f)

        assert left == right
        assert list(left) == [30, 40, 50]
        assert list(right) == [30, 40, 50]

    def test_functor_composition_single_element(self):
        def f(x: int) -> str:
            return f"value: {x}"

        def g(x: int) -> int:
            return x * 3

        nel = NonEmptyList(7, [])

        def composed(x: int) -> str:
            return f(g(x))

        left = nel.fmap(composed)
        right = nel.fmap(g).fmap(f)

        assert left == right
        assert list(left) == ["value: 21"]

    def test_functor_with_different_types(self):
        nel = NonEmptyList(1, [2, 3])
        mapped = nel.fmap(str)

        assert list(mapped) == ["1", "2", "3"]
        assert all(isinstance(x, str) for x in mapped)


class TestApplicativeLaws:
    """
    Applicative laws:
    1. Identity: pure(id) <*> v == v
    2. Composition: pure(.) <*> u <*> v <*> w == u <*> (v <*> w)
    3. Homomorphism: pure(f) <*> pure(x) == pure(f(x))
    4. Interchange: u <*> pure(y) == pure(lambda f: f(y)) <*> u
    """

    def test_applicative_identity(self):
        value = NonEmptyList(42, [10, 20])
        id_int: Callable[[int], int] = F.id
        funcs = NonEmptyList(id_int, [])

        result = value.ap(funcs)

        assert result == value
        assert list(result) == [42, 10, 20]

    def test_applicative_identity_single_element(self):
        value = NonEmptyList(99, [])
        id_int: Callable[[int], int] = F.id
        funcs = NonEmptyList(id_int, [])

        result = value.ap(funcs)

        assert result == value
        assert list(result) == [99]

    def test_applicative_homomorphism(self):
        def f(x: int) -> int:
            return x * 2

        x = 21

        left = NonEmptyList.pure(x).ap(NonEmptyList.pure(f))
        right = NonEmptyList.pure(f(x))

        assert left == right
        assert list(left) == [42]
        assert list(right) == [42]

    def test_applicative_interchange(self):
        def f(x: int) -> int:
            return x * 2

        def g(x: int) -> int:
            return x + 5

        y = 21

        funcs = NonEmptyList(f, [g])
        left = NonEmptyList.pure(y).ap(funcs)

        def apply_to_y(func: Callable[[int], int]) -> int:
            return func(y)

        right = funcs.ap(NonEmptyList.pure(apply_to_y))

        assert left == right
        assert list(left) == [42, 26]
        assert list(right) == [42, 26]

    def test_applicative_composition(self):
        def mul_two(x: int) -> int:
            return x * 2

        def add_ten(x: int) -> int:
            return x + 10

        u: NonEmptyList[Callable[[int], int]] = NonEmptyList(mul_two, [])
        v: NonEmptyList[Callable[[int], int]] = NonEmptyList(add_ten, [])
        w: NonEmptyList[int] = NonEmptyList(5, [10])

        left = w.ap(v).ap(u)
        right = w.ap(v.ap(u.ap(NonEmptyList.pure(F.compose))))

        assert left == right
        assert list(left) == [30, 40]
        assert list(right) == [30, 40]

    def test_applicative_multiple_functions(self):
        def double(x: int) -> int:
            return x * 2

        def triple(x: int) -> int:
            return x * 3

        values = NonEmptyList(5, [10])
        funcs = NonEmptyList(double, [triple])

        result = values.ap(funcs)

        assert list(result) == [10, 20, 15, 30]

    def test_applicative_cartesian_product(self):
        def add_prefix(x: str) -> str:
            return f"prefix_{x}"

        def add_suffix(x: str) -> str:
            return f"{x}_suffix"

        values = NonEmptyList("a", ["b", "c"])
        funcs = NonEmptyList(add_prefix, [add_suffix])

        result = values.ap(funcs)

        assert list(result) == [
            "prefix_a",
            "prefix_b",
            "prefix_c",
            "a_suffix",
            "b_suffix",
            "c_suffix",
        ]


class TestMonadLaws:
    """
    Monad laws:
    1. Left identity: pure(x).bind(f) == f(x)
    2. Right identity: m.bind(pure) == m
    3. Associativity: m.bind(f).bind(g) == m.bind(lambda x: f(x).bind(g))
    """

    def test_monad_left_identity(self):
        def f(a: int) -> NonEmptyList[int]:
            return NonEmptyList(a * 2, [a * 3])

        x = 42

        left = NonEmptyList.pure(x).bind(f)
        right = f(x)

        assert left == right
        assert list(left) == [84, 126]
        assert list(right) == [84, 126]

    def test_monad_left_identity_single_result(self):
        def f(a: int) -> NonEmptyList[int]:
            return NonEmptyList(a + 10, [])

        x = 5

        left = NonEmptyList.pure(x).bind(f)
        right = f(x)

        assert left == right
        assert list(left) == [15]

    def test_monad_right_identity(self):
        m = NonEmptyList(42, [10, 20])

        result = m.bind(NonEmptyList.pure)

        assert result == m
        assert list(result) == [42, 10, 20]

    def test_monad_right_identity_single_element(self):
        m = NonEmptyList(99, [])

        result = m.bind(NonEmptyList.pure)

        assert result == m
        assert list(result) == [99]

    def test_monad_associativity(self):
        def f(x: int) -> NonEmptyList[int]:
            return NonEmptyList(x + 10, [x + 20])

        def g(x: int) -> NonEmptyList[int]:
            return NonEmptyList(x * 2, [x * 3])

        m = NonEmptyList(5, [10])

        def bind_f_then_g(x: int) -> NonEmptyList[int]:
            return f(x).bind(g)

        left = m.bind(f).bind(g)
        right = m.bind(bind_f_then_g)

        assert left == right
        assert list(left) == list(right)

    def test_monad_associativity_complex(self):
        def f(x: int) -> NonEmptyList[str]:
            return NonEmptyList(str(x), [str(x * 2)])

        def g(s: str) -> NonEmptyList[int]:
            return NonEmptyList(len(s), [len(s) + 1])

        m = NonEmptyList(5, [10, 15])

        def bind_f_then_g(x: int) -> NonEmptyList[int]:
            return f(x).bind(g)

        left = m.bind(f).bind(g)
        right = m.bind(bind_f_then_g)

        assert left == right
        assert list(left) == list(right)

    def test_monad_bind_flattens(self):
        def duplicate(x: int) -> NonEmptyList[int]:
            return NonEmptyList(x, [x])

        nel = NonEmptyList(1, [2, 3])
        result = nel.bind(duplicate)

        assert list(result) == [1, 1, 2, 2, 3, 3]

    def test_monad_bind_with_varying_lengths(self):
        def expand(x: int) -> NonEmptyList[int]:
            return NonEmptyList(x, list(range(x)))

        nel = NonEmptyList(2, [3])
        result = nel.bind(expand)

        assert list(result) == [2, 0, 1, 3, 0, 1, 2]


class TestSemigroupLaws:
    """
    Semigroup laws:
    1. Associativity: (a <> b) <> c == a <> (b <> c)

    Note: NonEmptyList implements Semigroup via the op method.
    Since NonEmptyList is non-empty, it forms a Semigroup but not a Monoid
    (as there's no empty element to serve as identity).
    """

    def test_semigroup_associativity(self):
        a = NonEmptyList(1, [2])
        b = NonEmptyList(3, [4])
        c = NonEmptyList(5, [6])

        left = a.op(b).op(c)
        right = a.op(b.op(c))

        assert left == right
        assert list(left) == [1, 2, 3, 4, 5, 6]
        assert list(right) == [1, 2, 3, 4, 5, 6]

    def test_semigroup_associativity_single_elements(self):
        a = NonEmptyList(1, [])
        b = NonEmptyList(2, [])
        c = NonEmptyList(3, [])

        left = a.op(b).op(c)
        right = a.op(b.op(c))

        assert left == right
        assert list(left) == [1, 2, 3]
        assert list(right) == [1, 2, 3]

    def test_semigroup_associativity_mixed_lengths(self):
        a = NonEmptyList(1, [2, 3])
        b = NonEmptyList(4, [])
        c = NonEmptyList(5, [6, 7, 8])

        left = a.op(b).op(c)
        right = a.op(b.op(c))

        assert left == right
        assert list(left) == [1, 2, 3, 4, 5, 6, 7, 8]
        assert list(right) == [1, 2, 3, 4, 5, 6, 7, 8]

    def test_semigroup_op_via_add(self):
        a = NonEmptyList(1, [2])
        b = NonEmptyList(3, [4])

        result_op = a.op(b)
        result_add = a + b

        assert result_op == result_add
        assert list(result_op) == [1, 2, 3, 4]
        assert list(result_add) == [1, 2, 3, 4]

    def test_semigroup_multiple_operations(self):
        a = NonEmptyList(1, [])
        b = NonEmptyList(2, [])
        c = NonEmptyList(3, [])
        d = NonEmptyList(4, [])

        result = a.op(b).op(c).op(d)

        assert list(result) == [1, 2, 3, 4]

    def test_semigroup_with_strings(self):
        a = NonEmptyList("a", ["b"])
        b = NonEmptyList("c", ["d"])
        c = NonEmptyList("e", [])

        left = a.op(b).op(c)
        right = a.op(b.op(c))

        assert left == right
        assert list(left) == ["a", "b", "c", "d", "e"]
        assert list(right) == ["a", "b", "c", "d", "e"]


class TestNonEmptyListBasics:
    """
    Basic tests for NonEmptyList functionality.
    """

    def test_construction(self):
        nel = NonEmptyList(1, [2, 3])
        assert nel.head == 1
        assert nel.tail == [2, 3]
        assert list(nel) == [1, 2, 3]

    def test_construction_single_element(self):
        nel = NonEmptyList(42, [])
        assert nel.head == 42
        assert nel.tail == []
        assert list(nel) == [42]

    def test_pure(self):
        nel = NonEmptyList.pure(10)
        assert nel.head == 10
        assert nel.tail == []
        assert list(nel) == [10]

    def test_equality(self):
        nel1 = NonEmptyList(1, [2, 3])
        nel2 = NonEmptyList(1, [2, 3])
        nel3 = NonEmptyList(1, [2, 4])

        assert nel1 == nel2
        assert nel1 != nel3

    def test_hash(self):
        nel1 = NonEmptyList(1, [2, 3])
        nel2 = NonEmptyList(1, [2, 3])
        nel3 = NonEmptyList(1, [2, 4])

        assert hash(nel1) == hash(nel2)
        assert hash(nel1) != hash(nel3)

        s = {nel1, nel2, nel3}
        assert len(s) == 2

    def test_repr(self):
        nel = NonEmptyList(1, [2, 3])
        assert repr(nel) == "NonEmptyList([1, 2, 3])"
