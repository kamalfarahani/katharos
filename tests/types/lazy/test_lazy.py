import threading
import time
from collections.abc import Callable

import pytest

from katharos.concurrency import ThreadingBackend
from katharos.functools import F
from katharos.types.lazy import Lazy


class RecordingBackend(ThreadingBackend):
    """A ThreadingBackend that counts the locks it creates."""

    def __init__(self) -> None:
        self.locks_created = 0

    def create_lock(self):
        self.locks_created += 1
        return super().create_lock()


class TestLazyBackendPropagation:
    def test_fmap_uses_source_backend(self):
        backend = RecordingBackend()
        Lazy(fetcher=lambda: 1, backend=backend).fmap(lambda x: x + 1)

        assert backend.locks_created == 2

    def test_bind_uses_source_backend(self):
        backend = RecordingBackend()
        Lazy(fetcher=lambda: 1, backend=backend).bind(lambda x: Lazy.pure(x))

        assert backend.locks_created == 2

    def test_ap_uses_source_backend(self):
        backend = RecordingBackend()
        Lazy(fetcher=lambda: 1, backend=backend).ap(Lazy.pure(lambda x: x + 1))

        assert backend.locks_created == 2

    def test_chain_keeps_propagating_backend(self):
        backend = RecordingBackend()
        (
            Lazy(fetcher=lambda: 1, backend=backend)
            .fmap(lambda x: x + 1)
            .bind(lambda x: Lazy.pure(x))
        )

        assert backend.locks_created == 3


class TestLazyConstruction:
    def test_construction_with_fetcher(self):
        p = Lazy(fetcher=lambda: 42)

        assert isinstance(p, Lazy)

    def test_fetcher_not_called_on_construction(self):
        called = []
        Lazy(fetcher=lambda: called.append(1) or 42)

        assert called == []

    def test_pure_returns_lazy(self):
        p = Lazy.pure(42)

        assert isinstance(p, Lazy)

    def test_ret_returns_lazy(self):
        p = Lazy.ret(42)

        assert isinstance(p, Lazy)

    def test_pure_and_ret_are_equivalent(self):
        assert Lazy.pure(42).force() == Lazy.ret(42).force()


class TestLazyForcing:
    def test_force_returns_fetcher_value(self):
        p = Lazy(fetcher=lambda: 42)

        assert p.force() == 42

    def test_force_pure(self):
        assert Lazy.pure(99).force() == 99

    def test_force_ret(self):
        assert Lazy.ret("hello").force() == "hello"

    def test_force_memoizes_fetcher_result(self):
        counter = [0]

        def increment():
            counter[0] += 1
            return counter[0]

        p = Lazy(fetcher=increment)

        assert p.force() == 1
        assert p.force() == 1
        assert p.force() == 1
        assert counter[0] == 1

    def test_force_with_various_types(self):
        assert Lazy.pure([1, 2, 3]).force() == [1, 2, 3]
        assert Lazy.pure({"a": 1}).force() == {"a": 1}
        assert Lazy.pure(None).force() is None
        assert Lazy.pure(True).force() is True

    def test_force_memoizes_across_shared_upstream(self):
        counter = [0]

        def expensive():
            counter[0] += 1
            return counter[0]

        upstream = Lazy(fetcher=expensive)
        a = upstream.fmap(lambda x: x + 1)
        b = upstream.fmap(lambda x: x * 10)

        assert a.force() == 2
        assert b.force() == 10
        assert counter[0] == 1

    def test_force_propagates_fetcher_exception(self):
        def boom():
            raise ValueError("nope")

        p = Lazy(fetcher=boom)

        with pytest.raises(ValueError, match="nope"):
            p.force()

    def test_force_memoizes_fetcher_exception(self):
        counter = [0]

        def boom():
            counter[0] += 1
            raise ValueError("nope")

        p = Lazy(fetcher=boom)

        with pytest.raises(ValueError):
            p.force()
        with pytest.raises(ValueError):
            p.force()

        assert counter[0] == 1

    def test_force_runs_fetcher_once_under_concurrency(self):
        counter = [0]
        start = threading.Barrier(8)

        def slow():
            counter[0] += 1
            time.sleep(0.01)
            return counter[0]

        p = Lazy(fetcher=slow)
        results: list[int] = []

        def worker():
            # Line up all threads, then race into force() together.
            start.wait()
            results.append(p.force())

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert counter[0] == 1
        assert results == [1] * 8


class TestLazyResolveCompatibility:
    def test_resolve_and_force_share_cached_value(self):
        calls = []
        lazy = Lazy(fetcher=lambda: (calls.append(None), 42)[1])

        assert lazy.resolve() == 42
        assert lazy.force() == 42
        assert calls == [None]

    def test_resolve_and_force_share_cached_exception(self):
        calls = []
        error = ValueError("nope")

        def boom():
            calls.append(None)
            raise error

        lazy = Lazy(fetcher=boom)

        with pytest.raises(ValueError) as force_error:
            lazy.force()
        with pytest.raises(ValueError) as resolve_error:
            lazy.resolve()

        assert force_error.value is error
        assert resolve_error.value is error
        assert calls == [None]


class TestFunctorLaws:
    """
    Functor laws:
    1. Identity: fmap(id, x) == x
    2. Composition: fmap(f . g, x) == fmap(f, fmap(g, x))
    """

    def test_functor_identity(self):
        p = Lazy.pure(42)

        result = p.fmap(F.id)

        assert isinstance(result, Lazy)
        assert result.force() == p.force()

    def test_functor_composition(self):
        def f(x: int) -> int:
            return x * 2

        def g(x: int) -> int:
            return x + 10

        p = Lazy.pure(5)

        left = p.fmap(lambda x: f(g(x)))
        right = p.fmap(g).fmap(f)

        assert left.force() == right.force()
        assert left.force() == 30

    def test_fmap_is_lazy(self):
        called = []

        def f(x: int) -> int:
            called.append(x)
            return x * 2

        p = Lazy.pure(5).fmap(f)

        assert called == []
        assert p.force() == 10
        assert called == [5]

    def test_fmap_memoizes_on_force(self):
        calls = []

        def f(x: int) -> int:
            calls.append(x)
            return x * 2

        p = Lazy.pure(5).fmap(f)
        p.force()
        p.force()

        assert len(calls) == 1

    def test_fmap_type_transformation(self):
        p = Lazy.pure(42).fmap(str)

        assert p.force() == "42"
        assert isinstance(p.force(), str)

    def test_fmap_chain(self):
        result = Lazy.pure(1).fmap(lambda x: x + 9).fmap(lambda x: x * 3).fmap(str)

        assert result.force() == "30"


class TestApplicativeLaws:
    """
    Applicative laws:
    1. Identity:      v ** pure(id) == v
    2. Homomorphism:  pure(x) ** pure(f) == pure(f(x))
    3. Interchange:   pure(y) ** u == u ** pure(lambda f: f(y))
    4. Composition:   (w ** v) ** u == w ** (v ** (u ** pure(compose)))
    """

    def test_applicative_identity(self):
        p = Lazy.pure(42)
        id_func: Lazy[Callable[[int], int]] = Lazy.pure(F.id)

        result = p.ap(id_func)

        assert isinstance(result, Lazy)
        assert result.force() == p.force()

    def test_applicative_homomorphism(self):
        def f(x: int) -> int:
            return x * 2

        left = Lazy.pure(21).ap(Lazy.pure(f))
        right = Lazy.pure(f(21))

        assert left.force() == right.force()
        assert left.force() == 42

    def test_applicative_interchange(self):
        def f(x: int) -> int:
            return x * 2

        y = 21
        left = Lazy.pure(y).ap(Lazy.pure(f))

        def apply_to_y(g: Callable[[int], int]) -> int:
            return g(y)

        right = Lazy.pure(f).ap(Lazy.pure(apply_to_y))

        assert left.force() == right.force()
        assert left.force() == 42

    def test_applicative_composition(self):
        def mul_two(x: int) -> int:
            return x * 2

        def add_ten(x: int) -> int:
            return x + 10

        u: Lazy[Callable[[int], int]] = Lazy.pure(mul_two)
        v: Lazy[Callable[[int], int]] = Lazy.pure(add_ten)
        w: Lazy[int] = Lazy.pure(5)

        left = (w**v) ** u
        right = w ** (v ** (u ** Lazy.pure(F.compose)))

        assert left.force() == right.force()
        assert left.force() == 30

    def test_ap_applies_function_to_value(self):
        double = Lazy.pure(lambda x: x * 2)
        value = Lazy.pure(21)

        result = value.ap(double)

        assert result.force() == 42

    def test_ap_is_lazy(self):
        fetcher_calls = []
        func_calls = []

        def fetcher():
            fetcher_calls.append(1)
            return 10

        def func(x: int) -> int:
            func_calls.append(x)
            return x + 5

        result = Lazy(fetcher=fetcher).ap(Lazy.pure(func))

        assert fetcher_calls == []
        assert func_calls == []

        assert result.force() == 15
        assert len(fetcher_calls) == 1
        assert len(func_calls) == 1

    def test_ap_memoizes_on_force(self):
        calls = []
        counter = [0]

        def fetcher():
            counter[0] += 1
            return counter[0]

        def func(x: int) -> int:
            calls.append(x)
            return x * 10

        result = Lazy(fetcher=fetcher).ap(Lazy.pure(func))
        result.force()
        result.force()

        assert calls == [1]


class TestMonadLaws:
    """
    Monad laws:
    1. Left identity:  pure(a).bind(f) == f(a)
    2. Right identity: m.bind(pure) == m
    3. Associativity:  m.bind(f).bind(g) == m.bind(lambda x: f(x).bind(g))
    """

    def test_monad_left_identity(self):
        def f(x: int) -> Lazy[int]:
            return Lazy.pure(x * 2)

        left = Lazy.pure(21).bind(f)
        right = f(21)

        assert left.force() == right.force()
        assert left.force() == 42

    def test_monad_right_identity(self):
        m = Lazy.pure(42)

        result = m.bind(Lazy.pure)

        assert result.force() == m.force()

    def test_monad_associativity(self):
        def f(x: int) -> Lazy[int]:
            return Lazy.pure(x + 10)

        def g(x: int) -> Lazy[int]:
            return Lazy.pure(x * 2)

        m = Lazy.pure(5)

        left = m.bind(f).bind(g)
        right = m.bind(lambda x: f(x).bind(g))

        assert left.force() == right.force()
        assert left.force() == 30

    def test_bind_chains_computations(self):
        result = (
            Lazy.pure(3)
            .bind(lambda x: Lazy.pure(x * 10))
            .bind(lambda x: Lazy.pure(x + 2))
        )

        assert result.force() == 32

    def test_bind_is_lazy(self):
        fetcher_calls = []
        bind_calls = []

        def fetcher():
            fetcher_calls.append(1)
            return 5

        def f(x: int) -> Lazy[int]:
            bind_calls.append(x)
            return Lazy.pure(x * 2)

        result = Lazy(fetcher=fetcher).bind(f)

        assert fetcher_calls == []
        assert bind_calls == []

        assert result.force() == 10
        assert fetcher_calls == [1]
        assert bind_calls == [5]

    def test_bind_memoizes_on_force(self):
        counter = [0]
        bind_calls = []

        def fetcher():
            counter[0] += 1
            return counter[0]

        def f(x: int) -> Lazy[int]:
            bind_calls.append(x)
            return Lazy.pure(x * 10)

        result = Lazy(fetcher=fetcher).bind(f)
        result.force()
        result.force()

        assert bind_calls == [1]

    def test_bind_deep_chain(self):
        p = Lazy.pure(1)
        for i in range(1, 6):
            n = i
            p = p.bind(lambda x, n=n: Lazy.pure(x + n))

        assert p.force() == 16


class TestLazyOperators:
    def test_pow_operator_applies_function(self):
        value = Lazy.pure(21)
        func = Lazy.pure(lambda x: x * 2)

        result = value**func

        assert result.force() == 42

    def test_pow_operator_matches_ap(self):
        value = Lazy.pure(5)
        func = Lazy.pure(lambda x: x + 3)

        assert (value**func).force() == value.ap(func).force()

    def test_or_operator_binds(self):
        result = Lazy.pure(10) | (lambda x: Lazy.pure(x * 3))

        assert result.force() == 30

    def test_or_operator_matches_bind(self):
        def f(x: int) -> Lazy[int]:
            return Lazy.pure(x + 7)

        p = Lazy.pure(5)

        assert (p | f).force() == p.bind(f).force()

    def test_rshift_operator_sequences(self):
        first = Lazy.pure(1)
        second = Lazy.pure(99)

        result = first >> second

        assert result.force() == 99

    def test_rshift_discards_left_value(self):
        left_calls = []

        def left_fetcher():
            left_calls.append(1)
            return 42

        result = Lazy(fetcher=left_fetcher) >> Lazy.pure(99)

        assert result.force() == 99

    def test_rshift_evaluates_left_side(self):
        left_calls = []

        def left_fetcher():
            left_calls.append(1)
            return 42

        result = Lazy(fetcher=left_fetcher) >> Lazy.pure(99)
        result.force()

        assert left_calls == [1]

    def test_chained_operators(self):
        result = (
            Lazy.pure(2) | (lambda x: Lazy.pure(x * 5)) | (lambda x: Lazy.pure(x - 1))
        )

        assert result.force() == 9


class TestLazyLaziness:
    def test_construction_does_not_run_fetcher(self):
        side_effects = []
        Lazy(fetcher=lambda: side_effects.append(1) or 42)

        assert side_effects == []

    def test_fmap_does_not_run_fetcher(self):
        side_effects = []
        Lazy(fetcher=lambda: side_effects.append(1) or 42).fmap(lambda x: x)

        assert side_effects == []

    def test_bind_does_not_run_fetcher(self):
        side_effects = []
        Lazy(fetcher=lambda: side_effects.append(1) or 42).bind(Lazy.pure)

        assert side_effects == []

    def test_ap_does_not_run_fetcher(self):
        side_effects = []
        Lazy(fetcher=lambda: side_effects.append(1) or 42).ap(Lazy.pure(lambda x: x))

        assert side_effects == []

    def test_rshift_does_not_run_fetcher(self):
        side_effects = []
        _ = Lazy(fetcher=lambda: side_effects.append(1) or 42) >> Lazy.pure(99)

        assert side_effects == []

    def test_force_triggers_full_chain(self):
        log = []

        def step(label: str, value: int) -> int:
            log.append(label)
            return value

        result = (
            Lazy(fetcher=lambda: step("fetch", 1))
            .fmap(lambda x: step("fmap", x + 1))
            .bind(lambda x: Lazy(fetcher=lambda: step("bind", x * 3)))
        )

        assert log == []
        assert result.force() == 6
        assert log == ["fetch", "fmap", "bind"]


class TestLazyRepr:
    def test_repr_contains_lazy(self):
        p = Lazy.pure(42)

        assert repr(p).startswith("Lazy(")

    def test_repr_is_string(self):
        assert isinstance(repr(Lazy.pure(1)), str)
