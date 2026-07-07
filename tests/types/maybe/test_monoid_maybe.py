from katharos.types.list import NonEmptyList
from katharos.types.maybe import Maybe, MonoidMaybe


def test_left_identity_with_just():
    nel = NonEmptyList(1, [2, 3])
    a = MonoidMaybe(Maybe.Just(nel))
    identity = MonoidMaybe(Maybe.Nothing())

    result = identity @ a

    assert result.maybe == a.maybe


def test_right_identity_with_just():
    nel = NonEmptyList(1, [2, 3])
    a = MonoidMaybe(Maybe.Just(nel))
    identity = MonoidMaybe(Maybe.Nothing())

    result = a @ identity

    assert result.maybe == a.maybe


def test_left_identity_with_nothing():
    a = MonoidMaybe(Maybe.Nothing())
    identity = MonoidMaybe(Maybe.Nothing())

    result = identity @ a

    assert result.maybe == a.maybe


def test_right_identity_with_nothing():
    a = MonoidMaybe(Maybe.Nothing())
    identity = MonoidMaybe(Maybe.Nothing())

    result = a @ identity

    assert result.maybe == a.maybe


def test_associativity_all_just():
    nel1 = NonEmptyList(1, [2])
    nel2 = NonEmptyList(3, [4])
    nel3 = NonEmptyList(5, [6])

    a = MonoidMaybe(Maybe.Just(nel1))
    b = MonoidMaybe(Maybe.Just(nel2))
    c = MonoidMaybe(Maybe.Just(nel3))

    left = (a @ b) @ c
    right = a @ (b @ c)

    assert left.maybe == right.maybe


def test_associativity_first_nothing():
    nel2 = NonEmptyList(3, [4])
    nel3 = NonEmptyList(5, [6])

    a = MonoidMaybe(Maybe.Nothing())
    b = MonoidMaybe(Maybe.Just(nel2))
    c = MonoidMaybe(Maybe.Just(nel3))

    left = (a @ b) @ c
    right = a @ (b @ c)

    assert left.maybe == right.maybe


def test_associativity_second_nothing():
    nel1 = NonEmptyList(1, [2])
    nel3 = NonEmptyList(5, [6])

    a = MonoidMaybe(Maybe.Just(nel1))
    b = MonoidMaybe(Maybe.Nothing())
    c = MonoidMaybe(Maybe.Just(nel3))

    left = (a @ b) @ c
    right = a @ (b @ c)

    assert left.maybe == right.maybe


def test_associativity_third_nothing():
    nel1 = NonEmptyList(1, [2])
    nel2 = NonEmptyList(3, [4])

    a = MonoidMaybe(Maybe.Just(nel1))
    b = MonoidMaybe(Maybe.Just(nel2))
    c = MonoidMaybe(Maybe.Nothing())

    left = (a @ b) @ c
    right = a @ (b @ c)

    assert left.maybe == right.maybe


def test_associativity_all_nothing():
    a = MonoidMaybe(Maybe.Nothing())
    b = MonoidMaybe(Maybe.Nothing())
    c = MonoidMaybe(Maybe.Nothing())

    left = (a @ b) @ c
    right = a @ (b @ c)

    assert left.maybe == right.maybe


def test_semigroup_operation_combines_non_empty_lists():
    nel1 = NonEmptyList(1, [2])
    nel2 = NonEmptyList(3, [4])

    a = MonoidMaybe(Maybe.Just(nel1))
    b = MonoidMaybe(Maybe.Just(nel2))

    result = a @ b

    expected = NonEmptyList(1, [2, 3, 4])
    assert result.maybe == Maybe.Just(expected)


def test_nothing_with_just_returns_just():
    nel = NonEmptyList(1, [2, 3])
    nothing = MonoidMaybe(Maybe.Nothing())
    just = MonoidMaybe(Maybe.Just(nel))

    result1 = nothing @ just
    result2 = just @ nothing

    assert result1.maybe == Maybe.Just(nel)
    assert result2.maybe == Maybe.Just(nel)


def test_nothing_with_nothing_returns_nothing():
    a = MonoidMaybe(Maybe.Nothing())
    b = MonoidMaybe(Maybe.Nothing())

    result = a @ b

    assert result.maybe == Maybe.Nothing()


def test_repr_with_just():
    nel = NonEmptyList(1, [2, 3])
    a = MonoidMaybe(Maybe.Just(nel))
    assert repr(a) == f"MonoidMaybe(Just({nel!r}))"


def test_repr_with_nothing():
    a = MonoidMaybe(Maybe.Nothing())
    assert repr(a) == "MonoidMaybe(Nothing())"
