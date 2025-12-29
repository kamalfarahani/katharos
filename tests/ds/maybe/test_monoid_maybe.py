from katharos.ds.list import NonEmptyList
from katharos.ds.maybe import Just, MonoidMaybe, Nothing


def test_left_identity_with_just():
    nel = NonEmptyList(1, [2, 3])
    a = MonoidMaybe(Just(nel))
    identity = MonoidMaybe(Nothing())

    result = identity @ a

    assert result.maybe == a.maybe


def test_right_identity_with_just():
    nel = NonEmptyList(1, [2, 3])
    a = MonoidMaybe(Just(nel))
    identity = MonoidMaybe(Nothing())

    result = a @ identity

    assert result.maybe == a.maybe


def test_left_identity_with_nothing():
    a = MonoidMaybe(Nothing())
    identity = MonoidMaybe(Nothing())

    result = identity @ a

    assert result.maybe == a.maybe


def test_right_identity_with_nothing():
    a = MonoidMaybe(Nothing())
    identity = MonoidMaybe(Nothing())

    result = a @ identity

    assert result.maybe == a.maybe


def test_associativity_all_just():
    nel1 = NonEmptyList(1, [2])
    nel2 = NonEmptyList(3, [4])
    nel3 = NonEmptyList(5, [6])

    a = MonoidMaybe(Just(nel1))
    b = MonoidMaybe(Just(nel2))
    c = MonoidMaybe(Just(nel3))

    left = (a @ b) @ c
    right = a @ (b @ c)

    assert left.maybe == right.maybe


def test_associativity_first_nothing():
    nel2 = NonEmptyList(3, [4])
    nel3 = NonEmptyList(5, [6])

    a = MonoidMaybe(Nothing())
    b = MonoidMaybe(Just(nel2))
    c = MonoidMaybe(Just(nel3))

    left = (a @ b) @ c
    right = a @ (b @ c)

    assert left.maybe == right.maybe


def test_associativity_second_nothing():
    nel1 = NonEmptyList(1, [2])
    nel3 = NonEmptyList(5, [6])

    a = MonoidMaybe(Just(nel1))
    b = MonoidMaybe(Nothing())
    c = MonoidMaybe(Just(nel3))

    left = (a @ b) @ c
    right = a @ (b @ c)

    assert left.maybe == right.maybe


def test_associativity_third_nothing():
    nel1 = NonEmptyList(1, [2])
    nel2 = NonEmptyList(3, [4])

    a = MonoidMaybe(Just(nel1))
    b = MonoidMaybe(Just(nel2))
    c = MonoidMaybe(Nothing())

    left = (a @ b) @ c
    right = a @ (b @ c)

    assert left.maybe == right.maybe


def test_associativity_all_nothing():
    a = MonoidMaybe(Nothing())
    b = MonoidMaybe(Nothing())
    c = MonoidMaybe(Nothing())

    left = (a @ b) @ c
    right = a @ (b @ c)

    assert left.maybe == right.maybe


def test_semigroup_operation_combines_non_empty_lists():
    nel1 = NonEmptyList(1, [2])
    nel2 = NonEmptyList(3, [4])

    a = MonoidMaybe(Just(nel1))
    b = MonoidMaybe(Just(nel2))

    result = a @ b

    expected = NonEmptyList(1, [2, 3, 4])
    assert result.maybe == Just(expected)


def test_nothing_with_just_returns_just():
    nel = NonEmptyList(1, [2, 3])
    nothing = MonoidMaybe(Nothing())
    just = MonoidMaybe(Just(nel))

    result1 = nothing @ just
    result2 = just @ nothing

    assert result1.maybe == Just(nel)
    assert result2.maybe == Just(nel)


def test_nothing_with_nothing_returns_nothing():
    a = MonoidMaybe(Nothing())
    b = MonoidMaybe(Nothing())

    result = a @ b

    assert result.maybe == Nothing()
