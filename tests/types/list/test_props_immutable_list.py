"""Property-based tests for :class:`ImmutableList`.

These tests use Hypothesis to assert the algebraic laws and structural
invariants of :class:`ImmutableList` hold across a wide range of generated
inputs, complementing the worked-example tests in the other list modules.

:class:`ImmutableList` is both a :class:`~katharos.algebra.Monad` and a
:class:`~katharos.algebra.Monoid`, so both law sets are covered here. It has
a value-based ``__eq__`` (equal elements in the same order), so laws are
asserted directly on the lists. List sizes are kept small because ``ap``
forms a cartesian product, which the composition law nests.
"""

from hypothesis import given
from hypothesis import strategies as st

from katharos.types.list.immutable_list import ImmutableList
from tests.law_helpers import (
    check_applicative_laws,
    check_functor_laws,
    check_monad_laws,
    check_monoid_laws,
    unary_int_funcs as funcs,
)


def duplicate(x: int) -> ImmutableList[int]:
    return ImmutableList([x, x])


def drop(_: int) -> ImmutableList[int]:
    # Maps every element to the empty list.
    return ImmutableList([])


def range_to(x: int) -> ImmutableList[int]:
    return ImmutableList(range(abs(x) % 4))


# Strategies --------------------------------------------------------------

_ints = st.integers(min_value=-1000, max_value=1000)
# ImmutableList[int] values with bounded size (ap is a cartesian product).
ilists = st.lists(_ints, max_size=4).map(ImmutableList)
# Kleisli arrows int -> ImmutableList[int], sampled from a fixed pool.
kleislis = st.sampled_from(
    [duplicate, drop, range_to, lambda x: ImmutableList([x + 1])]
)
# ImmutableList of functions, bounded size.
ilist_funcs = st.lists(funcs, max_size=3).map(ImmutableList)


def test_functor_laws():
    check_functor_laws(ilists)


def test_applicative_laws():
    check_applicative_laws(ilists, ilist_funcs, ImmutableList.pure)


def test_monad_laws():
    check_monad_laws(ilists, kleislis, ImmutableList.pure)


def test_monoid_laws():
    check_monoid_laws(ilists, ImmutableList.identity)


@given(ilists, ilists)
def test_op_concatenates(xs: ImmutableList[int], ys: ImmutableList[int]):
    assert list(xs.op(ys)) == list(xs) + list(ys)


class TestStructuralProperties:
    @given(st.lists(_ints, max_size=8))
    def test_roundtrips_elements(self, elements: list[int]):
        xs = ImmutableList(elements)
        assert list(xs) == elements
        assert len(xs) == len(elements)

    @given(st.integers())
    def test_pure_is_singleton(self, x: int):
        assert ImmutableList.pure(x) == ImmutableList([x])
        assert len(ImmutableList.pure(x)) == 1

    @given(ilists, funcs)
    def test_fmap_preserves_length(self, xs: ImmutableList[int], f):
        assert len(xs.fmap(f)) == len(xs)

    @given(ilists, ilist_funcs)
    def test_ap_length_is_product(self, xs: ImmutableList[int], fs: ImmutableList):
        assert len(xs.ap(fs)) == len(xs) * len(fs)

    @given(ilists)
    def test_bind_empty_is_empty(self, xs: ImmutableList[int]):
        assert xs.bind(lambda _: ImmutableList([])) == ImmutableList([])

    @given(st.lists(_ints, max_size=8))
    def test_indexing_and_contains(self, elements: list[int]):
        xs = ImmutableList(elements)
        for i, elem in enumerate(elements):
            assert xs[i] == elem
            assert elem in xs


class TestOperatorEquivalence:
    @given(ilists, kleislis)
    def test_pipe_equals_bind(self, xs: ImmutableList[int], f):
        assert (xs | f) == xs.bind(f)

    @given(ilists, ilist_funcs)
    def test_pow_equals_ap(self, xs: ImmutableList[int], fs: ImmutableList):
        assert (xs**fs) == xs.ap(fs)

    @given(ilists, ilists)
    def test_matmul_equals_op(self, xs: ImmutableList[int], ys: ImmutableList[int]):
        assert (xs @ ys) == xs.op(ys)

    @given(ilists, ilists)
    def test_add_equals_op(self, xs: ImmutableList[int], ys: ImmutableList[int]):
        assert (xs + ys) == xs.op(ys)


class TestEqualityAndHash:
    @given(ilists)
    def test_reflexive(self, xs: ImmutableList[int]):
        assert xs == xs

    @given(st.lists(_ints, max_size=6), st.lists(_ints, max_size=6))
    def test_equal_iff_same_elements(self, a: list[int], b: list[int]):
        assert (ImmutableList(a) == ImmutableList(b)) == (a == b)

    @given(ilists)
    def test_not_equal_to_non_list(self, xs: ImmutableList[int]):
        assert xs != object()

    @given(ilists, ilists)
    def test_equal_implies_same_hash(
        self, xs: ImmutableList[int], ys: ImmutableList[int]
    ):
        if xs == ys:
            assert hash(xs) == hash(ys)
