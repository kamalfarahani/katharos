from hypothesis import given
from hypothesis import strategies as st

from katharos.functools import F
from katharos.types import Either
from tests.law_helpers import (
    check_applicative_laws,
    check_functor_laws,
    check_monad_laws,
    unary_int_funcs,
)


def only_positive(value: int) -> Either[str, int]:
    return Either.Right(value) if value > 0 else Either.Left("not positive")


def increment(value: int) -> Either[str, int]:
    return Either.Right(value + 1)


values = st.one_of(st.text().map(Either.Left), st.integers().map(Either.Right))
functions = st.one_of(st.text().map(Either.Left), unary_int_funcs.map(Either.Right))
kleislis = st.sampled_from([only_positive, increment])


def test_functor_laws():
    check_functor_laws(values)


def test_applicative_laws():
    check_applicative_laws(values, functions, Either.pure)


def test_monad_laws():
    check_monad_laws(values, kleislis, Either.pure)


@given(values, kleislis, functions, values)
def test_operators_match_methods(value, f, wrapped_function, other):
    assert (value | f) == value.bind(f)
    assert (value**wrapped_function) == value.ap(wrapped_function)
    assert (value >> other) == value.then(other)


@given(values)
def test_bimap_identity(value):
    assert value.bimap(F.id, F.id) == value


@given(values, unary_int_funcs, unary_int_funcs)
def test_bimap_composition(value, f, g):
    assert value.bimap(len, f).bimap(g, g) == value.bimap(
        lambda x: g(len(x)), lambda x: g(f(x))
    )


@given(values, unary_int_funcs)
def test_mapping_branches_separately_matches_bimap(value, f):
    assert value.map_left(len).fmap(f) == value.bimap(len, f)


@given(values)
def test_case_analysis_reconstructs_value(value):
    assert value.either(Either.Left, Either.Right) == value


@given(st.integers(), st.integers())
def test_equality_reflects_branch_and_payload(left, right):
    assert (Either.Left(left) == Either.Left(right)) == (left == right)
    assert (Either.Right(left) == Either.Right(right)) == (left == right)
    assert Either.Left(left) != Either.Right(right)
