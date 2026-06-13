import threading
import time
from collections.abc import Callable

import pytest

from katharos.functools import F
from katharos.types.promise import Promise


class TestPromiseConstruction:
    def test_construction_with_fetcher(self):
        p = Promise(fetcher=lambda: 42)

        assert isinstance(p, Promise)

    def test_fetcher_not_called_on_construction(self):
        called = []
        Promise(fetcher=lambda: called.append(1) or 42)

        assert called == []

    def test_pure_returns_promise(self):
        p = Promise.pure(42)

        assert isinstance(p, Promise)

    def test_ret_returns_promise(self):
        p = Promise.ret(42)

        assert isinstance(p, Promise)

    def test_pure_and_ret_are_equivalent(self):
        assert Promise.pure(42).resolve() == Promise.ret(42).resolve()


class TestPromiseResolution:
    def test_resolve_returns_fetcher_value(self):
        p = Promise(fetcher=lambda: 42)

        assert p.resolve() == 42

    def test_resolve_pure(self):
        assert Promise.pure(99).resolve() == 99

    def test_resolve_ret(self):
        assert Promise.ret("hello").resolve() == "hello"

    def test_resolve_memoizes_fetcher_result(self):
        counter = [0]

        def increment():
            counter[0] += 1
            return counter[0]

        p = Promise(fetcher=increment)

        assert p.resolve() == 1
        assert p.resolve() == 1
        assert p.resolve() == 1
        assert counter[0] == 1

    def test_resolve_with_various_types(self):
        assert Promise.pure([1, 2, 3]).resolve() == [1, 2, 3]
        assert Promise.pure({"a": 1}).resolve() == {"a": 1}
        assert Promise.pure(None).resolve() is None
        assert Promise.pure(True).resolve() is True

    def test_resolve_memoizes_across_shared_upstream(self):
        counter = [0]

        def expensive():
            counter[0] += 1
            return counter[0]

        upstream = Promise(fetcher=expensive)
        a = upstream.fmap(lambda x: x + 1)
        b = upstream.fmap(lambda x: x * 10)

        assert a.resolve() == 2
        assert b.resolve() == 10
        assert counter[0] == 1

    def test_resolve_propagates_fetcher_exception(self):
        def boom():
            raise ValueError("nope")

        p = Promise(fetcher=boom)

        with pytest.raises(ValueError, match="nope"):
            p.resolve()

    def test_resolve_memoizes_fetcher_exception(self):
        counter = [0]

        def boom():
            counter[0] += 1
            raise ValueError("nope")

        p = Promise(fetcher=boom)

        with pytest.raises(ValueError):
            p.resolve()
        with pytest.raises(ValueError):
            p.resolve()

        assert counter[0] == 1

    def test_resolve_runs_fetcher_once_under_concurrency(self):
        counter = [0]
        start = threading.Barrier(8)

        def slow():
            counter[0] += 1
            time.sleep(0.01)
            return counter[0]

        p = Promise(fetcher=slow)
        results: list[int] = []

        def worker():
            # Line up all threads, then race into resolve() together.
            start.wait()
            results.append(p.resolve())

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert counter[0] == 1
        assert results == [1] * 8


class TestPromiseGo:
    def test_go_returns_thread(self):
        p = Promise(fetcher=lambda: 42)

        t = p.go()
        t.join()

        assert isinstance(t, threading.Thread)

    def test_go_returns_alive_daemon_thread(self):
        started = threading.Event()
        release = threading.Event()

        def slow():
            started.set()
            release.wait()
            return 42

        p = Promise(fetcher=slow)
        t = p.go()

        started.wait()
        assert t.is_alive()
        assert t.daemon is True

        release.set()
        t.join()

    def test_go_resolves_in_background(self):
        p = Promise(fetcher=lambda: 42)

        t = p.go()
        t.join()

        assert p.resolve() == 42

    def test_go_runs_fetcher(self):
        called = threading.Event()

        def fetcher():
            called.set()
            return 42

        p = Promise(fetcher=fetcher)
        t = p.go()
        t.join()

        assert called.is_set()

    def test_go_does_not_block_caller(self):
        release = threading.Event()

        def slow():
            release.wait()
            return 42

        p = Promise(fetcher=slow)
        t = p.go()

        # Caller proceeds while the fetcher is still blocked.
        assert t.is_alive()

        release.set()
        t.join()
        assert p.resolve() == 42

    def test_resolve_after_go_reuses_cached_result(self):
        counter = [0]

        def increment():
            counter[0] += 1
            return counter[0]

        p = Promise(fetcher=increment)
        t = p.go()
        t.join()

        assert p.resolve() == 1
        assert p.resolve() == 1
        assert counter[0] == 1

    def test_go_runs_fetcher_once_across_resolve(self):
        counter = [0]

        def slow():
            counter[0] += 1
            time.sleep(0.01)
            return counter[0]

        p = Promise(fetcher=slow)
        t = p.go()
        # Race the main thread's resolve() against the background thread.
        result = p.resolve()
        t.join()

        assert result == 1
        assert counter[0] == 1

    def test_second_go_reuses_cached_result(self):
        counter = [0]

        def increment():
            counter[0] += 1
            return counter[0]

        p = Promise(fetcher=increment)
        first = p.go()
        first.join()
        second = p.go()
        second.join()

        assert p.resolve() == 1
        assert counter[0] == 1

    @pytest.mark.filterwarnings("ignore::pytest.PytestUnhandledThreadExceptionWarning")
    def test_go_caches_fetcher_exception(self):
        counter = [0]

        def boom():
            counter[0] += 1
            raise ValueError("nope")

        p = Promise(fetcher=boom)
        t = p.go()
        t.join()

        with pytest.raises(ValueError, match="nope"):
            p.resolve()
        assert counter[0] == 1


class TestFunctorLaws:
    """
    Functor laws:
    1. Identity: fmap(id, x) == x
    2. Composition: fmap(f . g, x) == fmap(f, fmap(g, x))
    """

    def test_functor_identity(self):
        p = Promise.pure(42)

        result = p.fmap(F.id)

        assert isinstance(result, Promise)
        assert result.resolve() == p.resolve()

    def test_functor_composition(self):
        def f(x: int) -> int:
            return x * 2

        def g(x: int) -> int:
            return x + 10

        p = Promise.pure(5)

        left = p.fmap(lambda x: f(g(x)))
        right = p.fmap(g).fmap(f)

        assert left.resolve() == right.resolve()
        assert left.resolve() == 30

    def test_fmap_is_lazy(self):
        called = []

        def f(x: int) -> int:
            called.append(x)
            return x * 2

        p = Promise.pure(5).fmap(f)

        assert called == []
        assert p.resolve() == 10
        assert called == [5]

    def test_fmap_memoizes_on_resolve(self):
        calls = []

        def f(x: int) -> int:
            calls.append(x)
            return x * 2

        p = Promise.pure(5).fmap(f)
        p.resolve()
        p.resolve()

        assert len(calls) == 1

    def test_fmap_type_transformation(self):
        p = Promise.pure(42).fmap(str)

        assert p.resolve() == "42"
        assert isinstance(p.resolve(), str)

    def test_fmap_chain(self):
        result = Promise.pure(1).fmap(lambda x: x + 9).fmap(lambda x: x * 3).fmap(str)

        assert result.resolve() == "30"


class TestApplicativeLaws:
    """
    Applicative laws:
    1. Identity:      v ** pure(id) == v
    2. Homomorphism:  pure(x) ** pure(f) == pure(f(x))
    3. Interchange:   pure(y) ** u == u ** pure(lambda f: f(y))
    4. Composition:   (w ** v) ** u == w ** (v ** (u ** pure(compose)))
    """

    def test_applicative_identity(self):
        p = Promise.pure(42)
        id_func: Promise[Callable[[int], int]] = Promise.pure(F.id)

        result = p.ap(id_func)

        assert isinstance(result, Promise)
        assert result.resolve() == p.resolve()

    def test_applicative_homomorphism(self):
        def f(x: int) -> int:
            return x * 2

        left = Promise.pure(21).ap(Promise.pure(f))
        right = Promise.pure(f(21))

        assert left.resolve() == right.resolve()
        assert left.resolve() == 42

    def test_applicative_interchange(self):
        def f(x: int) -> int:
            return x * 2

        y = 21
        left = Promise.pure(y).ap(Promise.pure(f))

        def apply_to_y(g: Callable[[int], int]) -> int:
            return g(y)

        right = Promise.pure(f).ap(Promise.pure(apply_to_y))

        assert left.resolve() == right.resolve()
        assert left.resolve() == 42

    def test_applicative_composition(self):
        def mul_two(x: int) -> int:
            return x * 2

        def add_ten(x: int) -> int:
            return x + 10

        u: Promise[Callable[[int], int]] = Promise.pure(mul_two)
        v: Promise[Callable[[int], int]] = Promise.pure(add_ten)
        w: Promise[int] = Promise.pure(5)

        left = (w**v) ** u
        right = w ** (v ** (u ** Promise.pure(F.compose)))

        assert left.resolve() == right.resolve()
        assert left.resolve() == 30

    def test_ap_applies_function_to_value(self):
        double = Promise.pure(lambda x: x * 2)
        value = Promise.pure(21)

        result = value.ap(double)

        assert result.resolve() == 42

    def test_ap_is_lazy(self):
        fetcher_calls = []
        func_calls = []

        def fetcher():
            fetcher_calls.append(1)
            return 10

        def func(x: int) -> int:
            func_calls.append(x)
            return x + 5

        result = Promise(fetcher=fetcher).ap(Promise.pure(func))

        assert fetcher_calls == []
        assert func_calls == []

        assert result.resolve() == 15
        assert len(fetcher_calls) == 1
        assert len(func_calls) == 1

    def test_ap_memoizes_on_resolve(self):
        calls = []
        counter = [0]

        def fetcher():
            counter[0] += 1
            return counter[0]

        def func(x: int) -> int:
            calls.append(x)
            return x * 10

        result = Promise(fetcher=fetcher).ap(Promise.pure(func))
        result.resolve()
        result.resolve()

        assert calls == [1]


class TestMonadLaws:
    """
    Monad laws:
    1. Left identity:  pure(a).bind(f) == f(a)
    2. Right identity: m.bind(pure) == m
    3. Associativity:  m.bind(f).bind(g) == m.bind(lambda x: f(x).bind(g))
    """

    def test_monad_left_identity(self):
        def f(x: int) -> Promise[int]:
            return Promise.pure(x * 2)

        left = Promise.pure(21).bind(f)
        right = f(21)

        assert left.resolve() == right.resolve()
        assert left.resolve() == 42

    def test_monad_right_identity(self):
        m = Promise.pure(42)

        result = m.bind(Promise.pure)

        assert result.resolve() == m.resolve()

    def test_monad_associativity(self):
        def f(x: int) -> Promise[int]:
            return Promise.pure(x + 10)

        def g(x: int) -> Promise[int]:
            return Promise.pure(x * 2)

        m = Promise.pure(5)

        left = m.bind(f).bind(g)
        right = m.bind(lambda x: f(x).bind(g))

        assert left.resolve() == right.resolve()
        assert left.resolve() == 30

    def test_bind_chains_computations(self):
        result = (
            Promise.pure(3)
            .bind(lambda x: Promise.pure(x * 10))
            .bind(lambda x: Promise.pure(x + 2))
        )

        assert result.resolve() == 32

    def test_bind_is_lazy(self):
        fetcher_calls = []
        bind_calls = []

        def fetcher():
            fetcher_calls.append(1)
            return 5

        def f(x: int) -> Promise[int]:
            bind_calls.append(x)
            return Promise.pure(x * 2)

        result = Promise(fetcher=fetcher).bind(f)

        assert fetcher_calls == []
        assert bind_calls == []

        assert result.resolve() == 10
        assert fetcher_calls == [1]
        assert bind_calls == [5]

    def test_bind_memoizes_on_resolve(self):
        counter = [0]
        bind_calls = []

        def fetcher():
            counter[0] += 1
            return counter[0]

        def f(x: int) -> Promise[int]:
            bind_calls.append(x)
            return Promise.pure(x * 10)

        result = Promise(fetcher=fetcher).bind(f)
        result.resolve()
        result.resolve()

        assert bind_calls == [1]

    def test_bind_deep_chain(self):
        p = Promise.pure(1)
        for i in range(1, 6):
            n = i
            p = p.bind(lambda x, n=n: Promise.pure(x + n))

        assert p.resolve() == 16


class TestPromiseOperators:
    def test_pow_operator_applies_function(self):
        value = Promise.pure(21)
        func = Promise.pure(lambda x: x * 2)

        result = value**func

        assert result.resolve() == 42

    def test_pow_operator_matches_ap(self):
        value = Promise.pure(5)
        func = Promise.pure(lambda x: x + 3)

        assert (value**func).resolve() == value.ap(func).resolve()

    def test_or_operator_binds(self):
        result = Promise.pure(10) | (lambda x: Promise.pure(x * 3))

        assert result.resolve() == 30

    def test_or_operator_matches_bind(self):
        def f(x: int) -> Promise[int]:
            return Promise.pure(x + 7)

        p = Promise.pure(5)

        assert (p | f).resolve() == p.bind(f).resolve()

    def test_rshift_operator_sequences(self):
        first = Promise.pure(1)
        second = Promise.pure(99)

        result = first >> second

        assert result.resolve() == 99

    def test_rshift_discards_left_value(self):
        left_calls = []

        def left_fetcher():
            left_calls.append(1)
            return 42

        result = Promise(fetcher=left_fetcher) >> Promise.pure(99)

        assert result.resolve() == 99

    def test_rshift_evaluates_left_side(self):
        left_calls = []

        def left_fetcher():
            left_calls.append(1)
            return 42

        result = Promise(fetcher=left_fetcher) >> Promise.pure(99)
        result.resolve()

        assert left_calls == [1]

    def test_chained_operators(self):
        result = (
            Promise.pure(2)
            | (lambda x: Promise.pure(x * 5))
            | (lambda x: Promise.pure(x - 1))
        )

        assert result.resolve() == 9


class TestPromiseLaziness:
    def test_construction_does_not_run_fetcher(self):
        side_effects = []
        Promise(fetcher=lambda: side_effects.append(1) or 42)

        assert side_effects == []

    def test_fmap_does_not_run_fetcher(self):
        side_effects = []
        Promise(fetcher=lambda: side_effects.append(1) or 42).fmap(lambda x: x)

        assert side_effects == []

    def test_bind_does_not_run_fetcher(self):
        side_effects = []
        Promise(fetcher=lambda: side_effects.append(1) or 42).bind(Promise.pure)

        assert side_effects == []

    def test_ap_does_not_run_fetcher(self):
        side_effects = []
        Promise(fetcher=lambda: side_effects.append(1) or 42).ap(
            Promise.pure(lambda x: x)
        )

        assert side_effects == []

    def test_rshift_does_not_run_fetcher(self):
        side_effects = []
        _ = Promise(fetcher=lambda: side_effects.append(1) or 42) >> Promise.pure(99)

        assert side_effects == []

    def test_resolve_triggers_full_chain(self):
        log = []

        def step(label: str, value: int) -> int:
            log.append(label)
            return value

        result = (
            Promise(fetcher=lambda: step("fetch", 1))
            .fmap(lambda x: step("fmap", x + 1))
            .bind(lambda x: Promise(fetcher=lambda: step("bind", x * 3)))
        )

        assert log == []
        assert result.resolve() == 6
        assert log == ["fetch", "fmap", "bind"]


class TestPromiseRepr:
    def test_repr_contains_promise(self):
        p = Promise.pure(42)

        assert repr(p).startswith("Promise(")

    def test_repr_is_string(self):
        assert isinstance(repr(Promise.pure(1)), str)
