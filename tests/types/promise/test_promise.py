from collections.abc import Callable

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
        assert Promise.pure(42).execute() == Promise.ret(42).execute()


class TestPromiseExecution:
    def test_execute_returns_fetcher_value(self):
        p = Promise(fetcher=lambda: 42)

        assert p.execute() == 42

    def test_execute_pure(self):
        assert Promise.pure(99).execute() == 99

    def test_execute_ret(self):
        assert Promise.ret("hello").execute() == "hello"

    def test_execute_reruns_fetcher_each_call(self):
        counter = [0]

        def increment():
            counter[0] += 1
            return counter[0]

        p = Promise(fetcher=increment)

        assert p.execute() == 1
        assert p.execute() == 2
        assert p.execute() == 3

    def test_execute_with_various_types(self):
        assert Promise.pure([1, 2, 3]).execute() == [1, 2, 3]
        assert Promise.pure({"a": 1}).execute() == {"a": 1}
        assert Promise.pure(None).execute() is None
        assert Promise.pure(True).execute() is True


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
        assert result.execute() == p.execute()

    def test_functor_composition(self):
        def f(x: int) -> int:
            return x * 2

        def g(x: int) -> int:
            return x + 10

        p = Promise.pure(5)

        left = p.fmap(lambda x: f(g(x)))
        right = p.fmap(g).fmap(f)

        assert left.execute() == right.execute()
        assert left.execute() == 30

    def test_fmap_is_lazy(self):
        called = []

        def f(x: int) -> int:
            called.append(x)
            return x * 2

        p = Promise.pure(5).fmap(f)

        assert called == []
        assert p.execute() == 10
        assert called == [5]

    def test_fmap_reruns_on_each_execute(self):
        calls = []

        def f(x: int) -> int:
            calls.append(x)
            return x * 2

        p = Promise.pure(5).fmap(f)
        p.execute()
        p.execute()

        assert len(calls) == 2

    def test_fmap_type_transformation(self):
        p = Promise.pure(42).fmap(str)

        assert p.execute() == "42"
        assert isinstance(p.execute(), str)

    def test_fmap_chain(self):
        result = Promise.pure(1).fmap(lambda x: x + 9).fmap(lambda x: x * 3).fmap(str)

        assert result.execute() == "30"


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
        assert result.execute() == p.execute()

    def test_applicative_homomorphism(self):
        def f(x: int) -> int:
            return x * 2

        left = Promise.pure(21).ap(Promise.pure(f))
        right = Promise.pure(f(21))

        assert left.execute() == right.execute()
        assert left.execute() == 42

    def test_applicative_interchange(self):
        def f(x: int) -> int:
            return x * 2

        y = 21
        left = Promise.pure(y).ap(Promise.pure(f))

        def apply_to_y(g: Callable[[int], int]) -> int:
            return g(y)

        right = Promise.pure(f).ap(Promise.pure(apply_to_y))

        assert left.execute() == right.execute()
        assert left.execute() == 42

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

        assert left.execute() == right.execute()
        assert left.execute() == 30

    def test_ap_applies_function_to_value(self):
        double = Promise.pure(lambda x: x * 2)
        value = Promise.pure(21)

        result = value.ap(double)

        assert result.execute() == 42

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

        assert result.execute() == 15
        assert len(fetcher_calls) == 1
        assert len(func_calls) == 1

    def test_ap_reruns_on_each_execute(self):
        calls = []
        counter = [0]

        def fetcher():
            counter[0] += 1
            return counter[0]

        def func(x: int) -> int:
            calls.append(x)
            return x * 10

        result = Promise(fetcher=fetcher).ap(Promise.pure(func))
        result.execute()
        result.execute()

        assert calls == [1, 2]


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

        assert left.execute() == right.execute()
        assert left.execute() == 42

    def test_monad_right_identity(self):
        m = Promise.pure(42)

        result = m.bind(Promise.pure)

        assert result.execute() == m.execute()

    def test_monad_associativity(self):
        def f(x: int) -> Promise[int]:
            return Promise.pure(x + 10)

        def g(x: int) -> Promise[int]:
            return Promise.pure(x * 2)

        m = Promise.pure(5)

        left = m.bind(f).bind(g)
        right = m.bind(lambda x: f(x).bind(g))

        assert left.execute() == right.execute()
        assert left.execute() == 30

    def test_bind_chains_computations(self):
        result = (
            Promise.pure(3)
            .bind(lambda x: Promise.pure(x * 10))
            .bind(lambda x: Promise.pure(x + 2))
        )

        assert result.execute() == 32

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

        assert result.execute() == 10
        assert fetcher_calls == [1]
        assert bind_calls == [5]

    def test_bind_reruns_on_each_execute(self):
        counter = [0]
        bind_calls = []

        def fetcher():
            counter[0] += 1
            return counter[0]

        def f(x: int) -> Promise[int]:
            bind_calls.append(x)
            return Promise.pure(x * 10)

        result = Promise(fetcher=fetcher).bind(f)
        result.execute()
        result.execute()

        assert bind_calls == [1, 2]

    def test_bind_deep_chain(self):
        p = Promise.pure(1)
        for i in range(1, 6):
            n = i
            p = p.bind(lambda x, n=n: Promise.pure(x + n))

        assert p.execute() == 16


class TestPromiseOperators:
    def test_pow_operator_applies_function(self):
        value = Promise.pure(21)
        func = Promise.pure(lambda x: x * 2)

        result = value**func

        assert result.execute() == 42

    def test_pow_operator_matches_ap(self):
        value = Promise.pure(5)
        func = Promise.pure(lambda x: x + 3)

        assert (value**func).execute() == value.ap(func).execute()

    def test_or_operator_binds(self):
        result = Promise.pure(10) | (lambda x: Promise.pure(x * 3))

        assert result.execute() == 30

    def test_or_operator_matches_bind(self):
        def f(x: int) -> Promise[int]:
            return Promise.pure(x + 7)

        p = Promise.pure(5)

        assert (p | f).execute() == p.bind(f).execute()

    def test_rshift_operator_sequences(self):
        first = Promise.pure(1)
        second = Promise.pure(99)

        result = first >> second

        assert result.execute() == 99

    def test_rshift_discards_left_value(self):
        left_calls = []

        def left_fetcher():
            left_calls.append(1)
            return 42

        result = Promise(fetcher=left_fetcher) >> Promise.pure(99)

        assert result.execute() == 99

    def test_rshift_evaluates_left_side(self):
        left_calls = []

        def left_fetcher():
            left_calls.append(1)
            return 42

        result = Promise(fetcher=left_fetcher) >> Promise.pure(99)
        result.execute()

        assert left_calls == [1]

    def test_chained_operators(self):
        result = (
            Promise.pure(2)
            | (lambda x: Promise.pure(x * 5))
            | (lambda x: Promise.pure(x - 1))
        )

        assert result.execute() == 9


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

    def test_execute_triggers_full_chain(self):
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
        assert result.execute() == 6
        assert log == ["fetch", "fmap", "bind"]


class TestPromiseRepr:
    def test_repr_contains_promise(self):
        p = Promise.pure(42)

        assert repr(p).startswith("Promise(")

    def test_repr_is_string(self):
        assert isinstance(repr(Promise.pure(1)), str)
