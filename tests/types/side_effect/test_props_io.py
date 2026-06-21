"""Property-based tests for :class:`IO`.

These tests use Hypothesis to assert the algebraic laws and side-effect
behaviour of :class:`IO` hold across a wide range of generated inputs,
complementing the worked-example tests in ``test_io.py``.

Note on equality: :class:`IO` has no value-based ``__eq__`` and wraps a
*deferred* side effect, so the algebraic laws are asserted on the resulting
``.value`` (as the existing example tests do). A separate set of tests covers
the effect dimension that ``.value`` cannot see: that constructing/composing
an ``IO`` runs nothing until :meth:`execute`, and that effects accumulate in
the right order.
"""

from hypothesis import given
from hypothesis import strategies as st

from katharos.functools import F
from katharos.types.side_effect import IO
from katharos.types.side_effect.function_with_side_effect import (
    FunctionWithSideEffect,
)


def add_one(x: int) -> int:
    return x + 1


def double(x: int) -> int:
    return x * 2


def negate(x: int) -> int:
    return -x


def to_io_plus_one(x: int) -> IO[int]:
    return IO(x + 1)


def to_io_double(x: int) -> IO[int]:
    return IO.pure(x * 2)


def to_io_square(x: int) -> IO[int]:
    return IO(x * x)


def recording_io(value: int, tag: object, log: list) -> IO[int]:
    """An IO whose deferred effect appends ``tag`` to ``log`` on execute."""
    return IO(value, FunctionWithSideEffect(f=lambda: log.append(tag)))


# Strategies --------------------------------------------------------------

# IO[int] values (no side effect).
ios = st.integers().map(IO)
# Pure unary functions int -> int, sampled from a fixed pool.
funcs = st.sampled_from([add_one, double, negate, lambda x: x, lambda x: x * x])
# Kleisli arrows int -> IO[int], sampled from a fixed pool.
kleislis = st.sampled_from([to_io_plus_one, to_io_double, to_io_square])
# IO wrapping a sampled function.
io_funcs = funcs.map(IO)


class TestFunctorLaws:
    @given(ios)
    def test_identity(self, io: IO[int]):
        assert io.fmap(F.id).value == io.value

    @given(ios, funcs, funcs)
    def test_composition(self, io: IO[int], f, g):
        left = io.fmap(lambda x: g(f(x)))
        right = io.fmap(f).fmap(g)
        assert left.value == right.value


class TestApplicativeLaws:
    @given(ios)
    def test_identity(self, v: IO[int]):
        assert v.ap(IO.pure(F.id)).value == v.value

    @given(st.integers(), funcs)
    def test_homomorphism(self, x: int, f):
        left = IO.pure(x).ap(IO.pure(f))
        right = IO.pure(f(x))
        assert left.value == right.value

    @given(st.integers(), io_funcs)
    def test_interchange(self, y: int, u: IO):
        left = IO.pure(y).ap(u)
        right = u.ap(IO.pure(lambda g: g(y)))
        assert left.value == right.value

    @given(io_funcs, io_funcs, ios)
    def test_composition(self, u: IO, v: IO, w: IO):
        left = w.ap(v).ap(u)
        right = w.ap(v.ap(u.ap(IO.pure(F.compose))))
        assert left.value == right.value


class TestMonadLaws:
    @given(st.integers(), kleislis)
    def test_left_identity(self, a: int, f):
        assert IO.pure(a).bind(f).value == f(a).value

    @given(ios)
    def test_right_identity(self, io: IO[int]):
        assert io.bind(IO.pure).value == io.value

    @given(ios, kleislis, kleislis)
    def test_associativity(self, io: IO[int], f, g):
        left = io.bind(f).bind(g)
        right = io.bind(lambda x: f(x).bind(g))
        assert left.value == right.value


class TestLaziness:
    @given(st.integers(), funcs, kleislis)
    def test_composition_runs_nothing(self, x: int, f, k):
        log: list = []
        base = recording_io(x, "base", log)
        # Building a whole chain triggers no side effect.
        _ = base.fmap(f).bind(k) >> IO.pure(0)
        assert log == []

    @given(st.integers())
    def test_pure_has_no_effect(self, x: int):
        # Executing a pure IO is observably a no-op.
        log: list = []
        io = IO.pure(x)
        io.execute()
        assert log == []


class TestSideEffectAccumulation:
    @given(st.lists(st.integers(), min_size=1, max_size=6))
    def test_then_accumulates_in_order(self, tags: list[int]):
        log: list = []
        # Sequence one recording IO per tag with >>.
        acc = recording_io(0, tags[0], log)
        for t in tags[1:]:
            acc = acc >> recording_io(0, t, log)

        assert log == []  # still deferred
        acc.execute()
        assert log == tags

    @given(st.integers(), st.integers())
    def test_bind_runs_self_then_continuation(self, a: int, b: int):
        log: list = []
        io = recording_io(a, "self", log)
        result = io.bind(lambda _: recording_io(b, "next", log))

        result.execute()
        assert log == ["self", "next"]

    @given(st.integers(), funcs)
    def test_fmap_preserves_self_effect(self, x: int, f):
        log: list = []
        io = recording_io(x, "self", log)
        mapped = io.fmap(f)

        assert mapped.value == f(x)
        mapped.execute()
        assert log == ["self"]

    @given(st.integers(), st.integers(min_value=1, max_value=4))
    def test_execute_reruns_effect_each_call(self, x: int, n: int):
        # execute() is not memoized: each call re-runs the effect.
        log: list = []
        io = recording_io(x, "tick", log)
        for _ in range(n):
            io.execute()
        assert log == ["tick"] * n


class TestOperatorEquivalence:
    @given(ios, kleislis)
    def test_pipe_equals_bind(self, io: IO[int], f):
        assert (io | f).value == io.bind(f).value

    @given(ios, io_funcs)
    def test_pow_equals_ap(self, io: IO[int], wf: IO):
        assert (io**wf).value == io.ap(wf).value

    @given(ios, ios)
    def test_rshift_equals_then(self, io: IO[int], other: IO[int]):
        assert (io >> other).value == io.then(other).value

    @given(ios, ios)
    def test_rshift_discards_left_value(self, io: IO[int], other: IO[int]):
        assert (io >> other).value == other.value


class TestPureAndRet:
    @given(st.integers())
    def test_pure_wraps_value(self, x: int):
        assert IO.pure(x).value == x

    @given(st.integers())
    def test_ret_equals_pure(self, x: int):
        assert IO.ret(x).value == IO.pure(x).value
