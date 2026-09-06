"""Reusable Hypothesis law-checkers for the property-based test suites.

The Functor / Applicative / Monad / Monoid / Semigroup laws are identical in
shape across every type in the library; only the strategies, the
``pure``/``identity`` constructor, and the way two wrapped values are compared
differ. These helpers capture the law assertions once so each type's test file
supplies only its own strategies plus an ``eq`` comparator.

Each ``check_*_laws`` helper is a plain function that defines ``@given``-decorated
inner closures and invokes them immediately. The helper itself is **not**
``@given``-decorated, so the inner properties are not nested inside another
Hypothesis run (nesting ``@given`` is disallowed and trips health checks).

Equality is injected via ``eq(a, b) -> bool`` and defaults to :func:`operator.eq`,
which is correct for the types that define a value-based ``__eq__`` (``Maybe``,
``Result``, ``ImmutableList``, ``NonEmptyList``). Types without one pass a custom
comparator, e.g. ``lambda a, b: a.force() == b.force()`` for ``Lazy``,
``lambda a, b: a.value == b.value`` for ``IO``, or a ``._value`` comparison
(optionally via :func:`pytest.approx`) for ``Sum``/``Product``.
"""

import operator
from collections.abc import Callable

from hypothesis import given
from hypothesis import strategies as st

from katharos.functools import F


def add_one(x: int) -> int:
    return x + 1


def double(x: int) -> int:
    return x * 2


def negate(x: int) -> int:
    return -x


# The standard pool of pure ``int -> int`` functions shared by every functor /
# applicative law check.
unary_int_funcs = st.sampled_from(
    [add_one, double, negate, lambda x: x, lambda x: x * x]
)


def check_functor_laws(
    values: st.SearchStrategy,
    funcs: st.SearchStrategy = unary_int_funcs,
    *,
    eq: Callable[[object, object], bool] = operator.eq,
) -> None:
    """Assert the two functor laws over ``values``.

    - Identity: ``m.fmap(id) == m``
    - Composition: ``m.fmap(g . f) == m.fmap(f).fmap(g)``
    """

    @given(values)
    def identity(m):
        assert eq(m.fmap(F.id), m)

    @given(values, funcs, funcs)
    def composition(m, f, g):
        assert eq(m.fmap(lambda x: g(f(x))), m.fmap(f).fmap(g))

    identity()
    composition()


def check_applicative_laws(
    values: st.SearchStrategy,
    wrapped_funcs: st.SearchStrategy,
    pure: Callable,
    *,
    funcs: st.SearchStrategy = unary_int_funcs,
    scalars: st.SearchStrategy = st.integers(),
    eq: Callable[[object, object], bool] = operator.eq,
) -> None:
    """Assert the four applicative laws.

    - Identity: ``v.ap(pure(id)) == v``
    - Homomorphism: ``pure(x).ap(pure(f)) == pure(f(x))``
    - Interchange: ``pure(y).ap(u) == u.ap(pure(lambda g: g(y)))``
    - Composition: ``w.ap(v).ap(u) == w.ap(v.ap(u.ap(pure(compose))))``
    """

    @given(values)
    def identity(v):
        assert eq(v.ap(pure(F.id)), v)

    @given(scalars, funcs)
    def homomorphism(x, f):
        assert eq(pure(x).ap(pure(f)), pure(f(x)))

    @given(scalars, wrapped_funcs)
    def interchange(y, u):
        assert eq(pure(y).ap(u), u.ap(pure(lambda g: g(y))))

    @given(wrapped_funcs, wrapped_funcs, values)
    def composition(u, v, w):
        left = w.ap(v).ap(u)
        right = w.ap(v.ap(u.ap(pure(F.compose))))
        assert eq(left, right)

    identity()
    homomorphism()
    interchange()
    composition()


def check_monad_laws(
    values: st.SearchStrategy,
    kleislis: st.SearchStrategy,
    pure: Callable,
    *,
    scalars: st.SearchStrategy = st.integers(),
    eq: Callable[[object, object], bool] = operator.eq,
) -> None:
    """Assert the three monad laws.

    - Left identity: ``pure(a).bind(f) == f(a)``
    - Right identity: ``m.bind(pure) == m``
    - Associativity: ``m.bind(f).bind(g) == m.bind(lambda x: f(x).bind(g))``
    """

    @given(scalars, kleislis)
    def left_identity(a, f):
        assert eq(pure(a).bind(f), f(a))

    @given(values)
    def right_identity(m):
        assert eq(m.bind(pure), m)

    @given(values, kleislis, kleislis)
    def associativity(m, f, g):
        left = m.bind(f).bind(g)
        right = m.bind(lambda x: f(x).bind(g))
        assert eq(left, right)

    left_identity()
    right_identity()
    associativity()


def check_semigroup_laws(
    values: st.SearchStrategy,
    *,
    eq: Callable[[object, object], bool] = operator.eq,
    combine: Callable = lambda a, b: a.op(b),
) -> None:
    """Assert semigroup associativity: ``(a <> b) <> c == a <> (b <> c)``."""

    @given(values, values, values)
    def associativity(a, b, c):
        left = combine(combine(a, b), c)
        right = combine(a, combine(b, c))
        assert eq(left, right)

    associativity()


def check_monoid_laws(
    values: st.SearchStrategy,
    identity: Callable[[], object],
    *,
    eq: Callable[[object, object], bool] = operator.eq,
    combine: Callable = lambda a, b: a.op(b),
) -> None:
    """Assert the monoid laws: semigroup associativity plus identity.

    - Left identity: ``identity() <> a == a``
    - Right identity: ``a <> identity() == a``

    Args:
        values: Strategy producing monoid elements.
        identity: Zero-argument callable returning the identity element (passed
            lazily so a parameterised identity such as ``Sum[int].identity`` can
            be supplied per element type).
        eq: Comparator for two combined elements.
        combine: The binary operation; defaults to ``a.op(b)``.
    """
    check_semigroup_laws(values, eq=eq, combine=combine)

    @given(values)
    def left_identity(a):
        assert eq(combine(identity(), a), a)

    @given(values)
    def right_identity(a):
        assert eq(combine(a, identity()), a)

    left_identity()
    right_identity()
