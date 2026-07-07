"""Property-based tests for :class:`MonoidMaybe`.

These tests use Hypothesis to assert the monoid laws of :class:`MonoidMaybe`
hold across a wide range of generated inputs, complementing the
worked-example tests in ``test_monoid_maybe.py``.

:class:`MonoidMaybe` lifts a :class:`~katharos.algebra.semigroup.Semigroup`
into an optional context; :class:`~katharos.types.list.NonEmptyList` is used
here as the wrapped semigroup. It has a value-based ``__eq__`` (delegating to
the wrapped ``Maybe``'s equality), so laws are asserted directly with no
custom comparator. List sizes are kept small purely for readability of
generated failures; there is no cartesian-product growth here since
``MonoidMaybe`` has no ``ap``.
"""

from hypothesis import given
from hypothesis import strategies as st

from katharos.types.list import NonEmptyList
from katharos.types.maybe import Maybe, MonoidMaybe
from tests.law_helpers import check_monoid_laws


def _nel(elements: list[int]) -> NonEmptyList[int]:
    return NonEmptyList(elements[0], elements[1:])


# Strategies --------------------------------------------------------------

_ints = st.integers(min_value=-1000, max_value=1000)
# NonEmptyList[int] values, bounded size.
nels = st.lists(_ints, min_size=1, max_size=4).map(_nel)
# MonoidMaybe[NonEmptyList[int]] values: Just(nel) or Nothing().
monoid_maybes = st.one_of(
    nels.map(lambda nel: MonoidMaybe(Maybe.Just(nel))),
    st.just(MonoidMaybe(Maybe.Nothing())),
)


def test_monoid_laws():
    check_monoid_laws(monoid_maybes, MonoidMaybe.identity)


class TestOperatorEquivalence:
    @given(monoid_maybes, monoid_maybes)
    def test_matmul_equals_op(self, a: MonoidMaybe, b: MonoidMaybe):
        assert (a @ b) == a.op(b)


class TestEqualityAndHash:
    @given(monoid_maybes)
    def test_reflexive(self, a: MonoidMaybe):
        assert a == a

    @given(monoid_maybes)
    def test_not_equal_to_non_monoid_maybe(self, a: MonoidMaybe):
        assert a != object()

    @given(monoid_maybes, monoid_maybes)
    def test_equal_implies_same_hash(self, a: MonoidMaybe, b: MonoidMaybe):
        if a == b:
            assert hash(a) == hash(b)
