from katharos.ds.list import NonEmptyList
from katharos.ds.maybe import Maybe, MonoidMaybe


def test_left_identity_with_just():
    nel = NonEmptyList(1, [2, 3])
    a = MonoidMaybe(Maybe(nel))
    identity = MonoidMaybe(Maybe())

    result = identity @ a

    assert result.maybe == a.maybe


def test_right_identity_with_just():
    nel = NonEmptyList(1, [2, 3])
    a = MonoidMaybe(Maybe(nel))
    identity = MonoidMaybe(Maybe())

    result = a @ identity

    assert result.maybe == a.maybe


def test_left_identity_with_nothing():
    a = MonoidMaybe(Maybe())
    identity = MonoidMaybe(Maybe())

    result = identity @ a

    assert result.maybe == a.maybe


def test_right_identity_with_nothing():
    a = MonoidMaybe(Maybe())
    identity = MonoidMaybe(Maybe())

    result = a @ identity

    assert result.maybe == a.maybe


def test_associativity_all_just():
    nel1 = NonEmptyList(1, [2])
    nel2 = NonEmptyList(3, [4])
    nel3 = NonEmptyList(5, [6])

    a = MonoidMaybe(Maybe(nel1))
    b = MonoidMaybe(Maybe(nel2))
    c = MonoidMaybe(Maybe(nel3))

    left = (a @ b) @ c
    right = a @ (b @ c)

    assert left.maybe == right.maybe


def test_associativity_first_nothing():
    nel2 = NonEmptyList(3, [4])
    nel3 = NonEmptyList(5, [6])

    a = MonoidMaybe(Maybe())
    b = MonoidMaybe(Maybe(nel2))
    c = MonoidMaybe(Maybe(nel3))

    left = (a @ b) @ c
    right = a @ (b @ c)

    assert left.maybe == right.maybe


def test_associativity_second_nothing():
    nel1 = NonEmptyList(1, [2])
    nel3 = NonEmptyList(5, [6])

    a = MonoidMaybe(Maybe(nel1))
    b = MonoidMaybe(Maybe())
    c = MonoidMaybe(Maybe(nel3))

    left = (a @ b) @ c
    right = a @ (b @ c)

    assert left.maybe == right.maybe


def test_associativity_third_nothing():
    nel1 = NonEmptyList(1, [2])
    nel2 = NonEmptyList(3, [4])

    a = MonoidMaybe(Maybe(nel1))
    b = MonoidMaybe(Maybe(nel2))
    c = MonoidMaybe(Maybe())

    left = (a @ b) @ c
    right = a @ (b @ c)

    assert left.maybe == right.maybe


def test_associativity_all_nothing():
    a = MonoidMaybe(Maybe())
    b = MonoidMaybe(Maybe())
    c = MonoidMaybe(Maybe())

    left = (a @ b) @ c
    right = a @ (b @ c)

    assert left.maybe == right.maybe


def test_semigroup_operation_combines_non_empty_lists():
    nel1 = NonEmptyList(1, [2])
    nel2 = NonEmptyList(3, [4])

    a = MonoidMaybe(Maybe(nel1))
    b = MonoidMaybe(Maybe(nel2))

    result = a @ b

    expected = NonEmptyList(1, [2, 3, 4])
    assert result.maybe == Maybe(expected)


def test_nothing_with_just_returns_just():
    nel = NonEmptyList(1, [2, 3])
    nothing = MonoidMaybe(Maybe())
    just = MonoidMaybe(Maybe(nel))

    result1 = nothing @ just
    result2 = just @ nothing

    assert result1.maybe == Maybe(nel)
    assert result2.maybe == Maybe(nel)


def test_nothing_with_nothing_returns_nothing():
    a = MonoidMaybe(Maybe())
    b = MonoidMaybe(Maybe())

    result = a @ b

    assert result.maybe == Maybe()
