"""Property-based tests for :class:`NonEmptyList`.

These tests use Hypothesis to assert the algebraic laws and structural
invariants of :class:`NonEmptyList` hold across a wide range of generated
inputs, complementing the worked-example tests in ``test_non_empty_list.py``.

:class:`NonEmptyList` is a :class:`~katharos.algebra.Monad` and a
:class:`~katharos.algebra.semigroup.Semigroup` but *not* a Monoid — there is
no empty list to serve as identity, so the monoid identity laws are absent.
It has a value-based ``__eq__`` (equal elements in the same order), so laws
are asserted directly on the lists. Every generated list has at least one
element. List sizes are kept small because ``ap`` forms a cartesian product,
which the composition law nests.
"""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from katharos.functools import F
from katharos.types.list.non_empty_list import NonEmptyList


def add_one(x: int) -> int:
    return x + 1


def double(x: int) -> int:
    return x * 2


def negate(x: int) -> int:
    return -x


def duplicate(x: int) -> NonEmptyList[int]:
    return NonEmptyList(x, [x])


def singleton_plus_one(x: int) -> NonEmptyList[int]:
    return NonEmptyList(x + 1, [])


def fan_out(x: int) -> NonEmptyList[int]:
    return NonEmptyList(x, [x + 1, x + 2])


def _nel(elements: list[int]) -> NonEmptyList[int]:
    return NonEmptyList(elements[0], elements[1:])


# Strategies --------------------------------------------------------------

_ints = st.integers(min_value=-1000, max_value=1000)
# NonEmptyList[int] values (always at least one element), bounded size
# because ap is a cartesian product.
nels = st.lists(_ints, min_size=1, max_size=4).map(_nel)
# Pure unary functions int -> int, sampled from a fixed pool.
funcs = st.sampled_from([add_one, double, negate, lambda x: x, lambda x: x * x])
# Kleisli arrows int -> NonEmptyList[int], sampled from a fixed pool.
kleislis = st.sampled_from([duplicate, singleton_plus_one, fan_out])
# NonEmptyList of functions, bounded size.
nel_funcs = st.lists(funcs, min_size=1, max_size=3).map(
    lambda fs: NonEmptyList(fs[0], fs[1:])
)


class TestFunctorLaws:
    @given(nels)
    def test_identity(self, xs: NonEmptyList[int]):
        assert xs.fmap(F.id) == xs

    @given(nels, funcs, funcs)
    def test_composition(self, xs: NonEmptyList[int], f, g):
        assert xs.fmap(lambda x: g(f(x))) == xs.fmap(f).fmap(g)


class TestApplicativeLaws:
    @given(nels)
    def test_identity(self, v: NonEmptyList[int]):
        assert v.ap(NonEmptyList.pure(F.id)) == v

    @given(st.integers(), funcs)
    def test_homomorphism(self, x: int, f):
        left = NonEmptyList.pure(x).ap(NonEmptyList.pure(f))
        right = NonEmptyList.pure(f(x))
        assert left == right

    @given(st.integers(), nel_funcs)
    def test_interchange(self, y: int, u: NonEmptyList):
        left = NonEmptyList.pure(y).ap(u)
        right = u.ap(NonEmptyList.pure(lambda g: g(y)))
        assert left == right

    @given(nel_funcs, nel_funcs, nels)
    def test_composition(self, u: NonEmptyList, v: NonEmptyList, w: NonEmptyList):
        left = w.ap(v).ap(u)
        right = w.ap(v.ap(u.ap(NonEmptyList.pure(F.compose))))
        assert left == right


class TestMonadLaws:
    @given(st.integers(), kleislis)
    def test_left_identity(self, a: int, f):
        assert NonEmptyList.pure(a).bind(f) == f(a)

    @given(nels)
    def test_right_identity(self, xs: NonEmptyList[int]):
        assert xs.bind(NonEmptyList.pure) == xs

    @given(nels, kleislis, kleislis)
    def test_associativity(self, xs: NonEmptyList[int], f, g):
        left = xs.bind(f).bind(g)
        right = xs.bind(lambda x: f(x).bind(g))
        assert left == right


class TestSemigroupLaws:
    @given(nels, nels, nels)
    def test_associativity(
        self, xs: NonEmptyList[int], ys: NonEmptyList[int], zs: NonEmptyList[int]
    ):
        assert (xs.op(ys)).op(zs) == xs.op(ys.op(zs))

    @given(nels, nels)
    def test_op_concatenates(self, xs: NonEmptyList[int], ys: NonEmptyList[int]):
        assert list(xs.op(ys)) == list(xs) + list(ys)


class TestStructuralProperties:
    @given(st.lists(_ints, min_size=1, max_size=8))
    def test_head_and_tail(self, elements: list[int]):
        xs = _nel(elements)
        assert xs.head == elements[0]
        assert xs.tail == elements[1:]
        # head prepended to tail reconstructs the whole list.
        assert [xs.head, *xs.tail] == list(xs)

    @given(nels)
    def test_never_empty(self, xs: NonEmptyList[int]):
        assert len(xs) >= 1

    @given(st.integers())
    def test_pure_is_singleton(self, x: int):
        xs = NonEmptyList.pure(x)
        assert xs == NonEmptyList(x, [])
        assert len(xs) == 1
        assert xs.head == x
        assert xs.tail == []

    @given(nels, funcs)
    def test_fmap_preserves_length(self, xs: NonEmptyList[int], f):
        assert len(xs.fmap(f)) == len(xs)

    @given(nels, nel_funcs)
    def test_ap_length_is_product(self, xs: NonEmptyList[int], fs: NonEmptyList):
        assert len(xs.ap(fs)) == len(xs) * len(fs)

    @given(nels, kleislis)
    def test_bind_length_is_sum(self, xs: NonEmptyList[int], f):
        assert len(xs.bind(f)) == sum(len(f(x)) for x in xs)


class TestOperatorEquivalence:
    @given(nels, kleislis)
    def test_pipe_equals_bind(self, xs: NonEmptyList[int], f):
        assert (xs | f) == xs.bind(f)

    @given(nels, nel_funcs)
    def test_pow_equals_ap(self, xs: NonEmptyList[int], fs: NonEmptyList):
        assert (xs**fs) == xs.ap(fs)

    @given(nels, nels)
    def test_matmul_equals_op(self, xs: NonEmptyList[int], ys: NonEmptyList[int]):
        assert (xs @ ys) == xs.op(ys)

    @given(nels, nels)
    def test_add_equals_op(self, xs: NonEmptyList[int], ys: NonEmptyList[int]):
        assert (xs + ys) == xs.op(ys)


class TestEqualityAndHash:
    @given(nels)
    def test_reflexive(self, xs: NonEmptyList[int]):
        assert xs == xs

    @given(
        st.lists(_ints, min_size=1, max_size=6),
        st.lists(_ints, min_size=1, max_size=6),
    )
    def test_equal_iff_same_elements(self, a: list[int], b: list[int]):
        assert (_nel(a) == _nel(b)) == (a == b)

    @given(nels)
    def test_not_equal_to_non_nel(self, xs: NonEmptyList[int]):
        assert xs != object()

    @given(nels, nels)
    def test_equal_implies_same_hash(
        self, xs: NonEmptyList[int], ys: NonEmptyList[int]
    ):
        if xs == ys:
            assert hash(xs) == hash(ys)


class TestConstruction:
    def test_requires_head(self):
        # The constructor takes a mandatory head, so a NonEmptyList can never
        # be built empty.
        with pytest.raises(TypeError):
            NonEmptyList()  # type: ignore[call-arg]
