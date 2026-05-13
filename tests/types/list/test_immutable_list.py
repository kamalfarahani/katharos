from collections.abc import Callable

from katharos.types.list.immutable_list import ImmutableList
from katharos.functools import F


class TestFunctorLaws:
    """
    Functor laws:
    1. Identity: fmap(id, x) == x
    2. Composition: fmap(f . g, x) == fmap(f, fmap(g, x))
    """

    def test_functor_identity(self):
        lst = ImmutableList([1, 2, 3, 4])

        mapped = lst.fmap(F.id)

        assert mapped == lst
        assert list(mapped) == [1, 2, 3, 4]

    def test_functor_identity_empty(self):
        lst = ImmutableList([])

        mapped = lst.fmap(F.id)

        assert mapped == lst
        assert list(mapped) == []

    def test_functor_identity_single_element(self):
        lst = ImmutableList([42])

        mapped = lst.fmap(F.id)

        assert mapped == lst
        assert list(mapped) == [42]

    def test_functor_composition(self):
        def f(x: int) -> int:
            return x * 2

        def g(x: int) -> int:
            return x + 10

        lst = ImmutableList([5, 10, 15])

        def composed(x: int) -> int:
            return f(g(x))

        left = lst.fmap(composed)
        right = lst.fmap(g).fmap(f)

        assert left == right
        assert list(left) == [30, 40, 50]
        assert list(right) == [30, 40, 50]

    def test_functor_composition_empty(self):
        def f(x: int) -> int:
            return x * 2

        def g(x: int) -> int:
            return x + 10

        lst = ImmutableList([])

        def composed(x: int) -> int:
            return f(g(x))

        left = lst.fmap(composed)
        right = lst.fmap(g).fmap(f)

        assert left == right
        assert list(left) == []
        assert list(right) == []

    def test_functor_composition_type_change(self):
        def f(x: int) -> str:
            return f"value: {x}"

        def g(x: int) -> int:
            return x * 3

        lst = ImmutableList([7, 14])

        def composed(x: int) -> str:
            return f(g(x))

        left = lst.fmap(composed)
        right = lst.fmap(g).fmap(f)

        assert left == right
        assert list(left) == ["value: 21", "value: 42"]

    def test_functor_with_different_types(self):
        lst = ImmutableList([1, 2, 3])
        mapped = lst.fmap(str)

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
        value = ImmutableList([42, 10, 20])
        id_int: Callable[[int], int] = F.id
        funcs = ImmutableList([id_int])

        result = value.ap(funcs)

        assert result == value
        assert list(result) == [42, 10, 20]

    def test_applicative_identity_empty(self):
        value = ImmutableList([])
        id_int: Callable[[int], int] = F.id
        funcs = ImmutableList([id_int])

        result = value.ap(funcs)

        assert result == value
        assert list(result) == []

    def test_applicative_identity_single_element(self):
        value = ImmutableList([99])
        id_int: Callable[[int], int] = F.id
        funcs = ImmutableList([id_int])

        result = value.ap(funcs)

        assert result == value
        assert list(result) == [99]

    def test_applicative_homomorphism(self):
        def f(x: int) -> int:
            return x * 2

        x = 21

        left = ImmutableList.pure(x).ap(ImmutableList.pure(f))
        right = ImmutableList.pure(f(x))

        assert left == right
        assert list(left) == [42]
        assert list(right) == [42]

    def test_applicative_interchange(self):
        def f(x: int) -> int:
            return x * 2

        def g(x: int) -> int:
            return x + 5

        y = 21

        funcs = ImmutableList([f, g])
        left = ImmutableList.pure(y).ap(funcs)

        def apply_to_y(func: Callable[[int], int]) -> int:
            return func(y)

        right = funcs.ap(ImmutableList.pure(apply_to_y))

        assert left == right
        assert list(left) == [42, 26]
        assert list(right) == [42, 26]

    def test_applicative_composition(self):
        def mul_two(x: int) -> int:
            return x * 2

        def add_ten(x: int) -> int:
            return x + 10

        u: ImmutableList[Callable[[int], int]] = ImmutableList([mul_two])
        v: ImmutableList[Callable[[int], int]] = ImmutableList([add_ten])
        w: ImmutableList[int] = ImmutableList([5, 10])

        left = w.ap(v).ap(u)
        right = w.ap(v.ap(u.ap(ImmutableList.pure(F.compose))))

        assert left == right
        assert list(left) == [30, 40]
        assert list(right) == [30, 40]

    def test_applicative_multiple_functions(self):
        def double(x: int) -> int:
            return x * 2

        def triple(x: int) -> int:
            return x * 3

        values = ImmutableList([5, 10])
        funcs = ImmutableList([double, triple])

        result = values.ap(funcs)

        assert list(result) == [10, 20, 15, 30]

    def test_applicative_cartesian_product(self):
        def add_prefix(x: str) -> str:
            return f"prefix_{x}"

        def add_suffix(x: str) -> str:
            return f"{x}_suffix"

        values = ImmutableList(["a", "b", "c"])
        funcs = ImmutableList([add_prefix, add_suffix])

        result = values.ap(funcs)

        assert list(result) == [
            "prefix_a",
            "prefix_b",
            "prefix_c",
            "a_suffix",
            "b_suffix",
            "c_suffix",
        ]

    def test_applicative_empty_values(self):
        def f(x: int) -> int:
            return x * 2

        values = ImmutableList([])
        funcs = ImmutableList([f])

        result = values.ap(funcs)

        assert list(result) == []

    def test_applicative_empty_functions(self):
        values = ImmutableList([1, 2, 3])
        funcs: ImmutableList[Callable[[int], int]] = ImmutableList([])

        result = values.ap(funcs)

        assert list(result) == []


class TestMonadLaws:
    """
    Monad laws:
    1. Left identity: pure(x).bind(f) == f(x)
    2. Right identity: m.bind(pure) == m
    3. Associativity: m.bind(f).bind(g) == m.bind(lambda x: f(x).bind(g))
    """

    def test_monad_left_identity(self):
        def f(a: int) -> ImmutableList[int]:
            return ImmutableList([a * 2, a * 3])

        x = 42

        left = ImmutableList.pure(x).bind(f)
        right = f(x)

        assert left == right
        assert list(left) == [84, 126]
        assert list(right) == [84, 126]

    def test_monad_left_identity_empty_result(self):
        def f(a: int) -> ImmutableList[int]:
            return ImmutableList([])

        x = 5

        left = ImmutableList.pure(x).bind(f)
        right = f(x)

        assert left == right
        assert list(left) == []

    def test_monad_left_identity_single_result(self):
        def f(a: int) -> ImmutableList[int]:
            return ImmutableList([a + 10])

        x = 5

        left = ImmutableList.pure(x).bind(f)
        right = f(x)

        assert left == right
        assert list(left) == [15]

    def test_monad_right_identity(self):
        m = ImmutableList([42, 10, 20])

        result = m.bind(ImmutableList.pure)

        assert result == m
        assert list(result) == [42, 10, 20]

    def test_monad_right_identity_empty(self):
        m = ImmutableList([])

        result = m.bind(ImmutableList.pure)

        assert result == m
        assert list(result) == []

    def test_monad_right_identity_single_element(self):
        m = ImmutableList([99])

        result = m.bind(ImmutableList.pure)

        assert result == m
        assert list(result) == [99]

    def test_monad_associativity(self):
        def f(x: int) -> ImmutableList[int]:
            return ImmutableList([x + 10, x + 20])

        def g(x: int) -> ImmutableList[int]:
            return ImmutableList([x * 2, x * 3])

        m = ImmutableList([5, 10])

        def bind_f_then_g(x: int) -> ImmutableList[int]:
            return f(x).bind(g)

        left = m.bind(f).bind(g)
        right = m.bind(bind_f_then_g)

        assert left == right
        assert list(left) == list(right)

    def test_monad_associativity_empty(self):
        def f(x: int) -> ImmutableList[int]:
            return ImmutableList([x + 10])

        def g(x: int) -> ImmutableList[int]:
            return ImmutableList([x * 2])

        m = ImmutableList([])

        def bind_f_then_g(x: int) -> ImmutableList[int]:
            return f(x).bind(g)

        left = m.bind(f).bind(g)
        right = m.bind(bind_f_then_g)

        assert left == right
        assert list(left) == []
        assert list(right) == []

    def test_monad_associativity_complex(self):
        def f(x: int) -> ImmutableList[str]:
            return ImmutableList([str(x), str(x * 2)])

        def g(s: str) -> ImmutableList[int]:
            return ImmutableList([len(s), len(s) + 1])

        m = ImmutableList([5, 10, 15])

        def bind_f_then_g(x: int) -> ImmutableList[int]:
            return f(x).bind(g)

        left = m.bind(f).bind(g)
        right = m.bind(bind_f_then_g)

        assert left == right
        assert list(left) == list(right)

    def test_monad_bind_flattens(self):
        def duplicate(x: int) -> ImmutableList[int]:
            return ImmutableList([x, x])

        lst = ImmutableList([1, 2, 3])
        result = lst.bind(duplicate)

        assert list(result) == [1, 1, 2, 2, 3, 3]

    def test_monad_bind_with_varying_lengths(self):
        def expand(x: int) -> ImmutableList[int]:
            return ImmutableList([x] + list(range(x)))

        lst = ImmutableList([2, 3])
        result = lst.bind(expand)

        assert list(result) == [2, 0, 1, 3, 0, 1, 2]

    def test_monad_bind_to_empty(self):
        def always_empty(x: int) -> ImmutableList[int]:
            return ImmutableList([])

        lst = ImmutableList([1, 2, 3])
        result = lst.bind(always_empty)

        assert list(result) == []


class TestMonoidLaws:
    """
    Monoid laws:
    1. Left identity: identity <> x == x
    2. Right identity: x <> identity == x
    3. Associativity: (x <> y) <> z == x <> (y <> z)
    """

    def test_monoid_left_identity(self):
        x = ImmutableList([1, 2, 3])
        identity = ImmutableList.identity()

        result = identity.op(x)

        assert result == x
        assert list(result) == [1, 2, 3]

    def test_monoid_left_identity_empty(self):
        x = ImmutableList([])
        identity = ImmutableList.identity()

        result = identity.op(x)

        assert result == x
        assert list(result) == []

    def test_monoid_right_identity(self):
        x = ImmutableList([1, 2, 3])
        identity = ImmutableList.identity()

        result = x.op(identity)

        assert result == x
        assert list(result) == [1, 2, 3]

    def test_monoid_right_identity_empty(self):
        x = ImmutableList([])
        identity = ImmutableList.identity()

        result = x.op(identity)

        assert result == x
        assert list(result) == []

    def test_monoid_associativity(self):
        a = ImmutableList([1, 2])
        b = ImmutableList([3, 4])
        c = ImmutableList([5, 6])

        left = a.op(b).op(c)
        right = a.op(b.op(c))

        assert left == right
        assert list(left) == [1, 2, 3, 4, 5, 6]
        assert list(right) == [1, 2, 3, 4, 5, 6]

    def test_monoid_associativity_with_empty(self):
        a = ImmutableList([1, 2])
        b = ImmutableList([])
        c = ImmutableList([3, 4])

        left = a.op(b).op(c)
        right = a.op(b.op(c))

        assert left == right
        assert list(left) == [1, 2, 3, 4]
        assert list(right) == [1, 2, 3, 4]

    def test_monoid_associativity_all_empty(self):
        a = ImmutableList([])
        b = ImmutableList([])
        c = ImmutableList([])

        left = a.op(b).op(c)
        right = a.op(b.op(c))

        assert left == right
        assert list(left) == []
        assert list(right) == []

    def test_monoid_op_via_add(self):
        a = ImmutableList([1, 2])
        b = ImmutableList([3, 4])

        result_op = a.op(b)
        result_add = a + b

        assert result_op == result_add
        assert list(result_op) == [1, 2, 3, 4]
        assert list(result_add) == [1, 2, 3, 4]

    def test_monoid_multiple_operations(self):
        a = ImmutableList([1])
        b = ImmutableList([2])
        c = ImmutableList([3])
        d = ImmutableList([4])

        result = a.op(b).op(c).op(d)

        assert list(result) == [1, 2, 3, 4]

    def test_monoid_with_strings(self):
        a = ImmutableList(["a", "b"])
        b = ImmutableList(["c", "d"])
        c = ImmutableList(["e"])

        left = a.op(b).op(c)
        right = a.op(b.op(c))

        assert left == right
        assert list(left) == ["a", "b", "c", "d", "e"]
        assert list(right) == ["a", "b", "c", "d", "e"]

    def test_monoid_identity_is_empty(self):
        identity = ImmutableList.identity()
        assert list(identity) == []
        assert identity == ImmutableList([])


class TestImmutableListBasics:
    """
    Basic tests for ImmutableList functionality.
    """

    def test_construction(self):
        lst = ImmutableList([1, 2, 3])
        assert list(lst) == [1, 2, 3]

    def test_construction_empty(self):
        lst = ImmutableList([])
        assert list(lst) == []

    def test_pure(self):
        lst = ImmutableList.pure(10)
        assert list(lst) == [10]

    def test_equality(self):
        lst1 = ImmutableList([1, 2, 3])
        lst2 = ImmutableList([1, 2, 3])
        lst3 = ImmutableList([1, 2, 4])

        assert lst1 == lst2
        assert lst1 != lst3

    def test_equality_empty(self):
        lst1 = ImmutableList([])
        lst2 = ImmutableList([])

        assert lst1 == lst2

    def test_hash(self):
        lst1 = ImmutableList([1, 2, 3])
        lst2 = ImmutableList([1, 2, 3])
        lst3 = ImmutableList([1, 2, 4])

        assert hash(lst1) == hash(lst2)
        assert hash(lst1) != hash(lst3)

        s = {lst1, lst2, lst3}
        assert len(s) == 2

    def test_hash_empty(self):
        lst1 = ImmutableList([])
        lst2 = ImmutableList([])

        assert hash(lst1) == hash(lst2)

    def test_repr(self):
        lst = ImmutableList([1, 2, 3])
        assert repr(lst) == "ImmutableList([1, 2, 3])"

    def test_repr_empty(self):
        lst = ImmutableList([])
        assert repr(lst) == "ImmutableList([])"

    def test_str(self):
        lst = ImmutableList([1, 2, 3])
        assert str(lst) == "[1, 2, 3]"

    def test_add_with_list(self):
        lst = ImmutableList([1, 2])
        result = lst + [3, 4]
        assert list(result) == [1, 2, 3, 4]
        assert isinstance(result, ImmutableList)
