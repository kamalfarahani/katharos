from katharos.ds.maybe.maybe import Just, Maybe, Nothing
from katharos.functools import F


def add_one(x: float) -> float:
    return x + 1


def multiply_by_two(x: float) -> float:
    return x * 2


def to_string(x: float) -> str:
    return str(x)


def safe_divide(x: float) -> Maybe[float]:
    if x == 0:
        return Nothing()
    return Just(10.0 / x)


def safe_sqrt(x: float) -> Maybe[float]:
    if x < 0:
        return Nothing()
    return Just(x**0.5)


class TestMaybeBasics:
    def test_just_creation(self):
        m = Just(5)
        assert m.value == 5

    def test_nothing_creation(self):
        m = Nothing()
        assert isinstance(m, Nothing)

    def test_pure(self):
        m = Maybe.pure(42)
        assert isinstance(m, Just)
        assert m.value == 42


class TestFunctorLaws:
    """
    Functor laws:
    1. Identity: fmap id = id
    2. Composition: fmap (g . f) = fmap g . fmap f
    """

    def test_functor_identity_just(self):
        m = Just(10)
        assert m.fmap(F.id).value == m.value

    def test_functor_identity_nothing(self):
        m = Nothing()
        result = m.fmap(F.id)
        assert isinstance(result, Nothing)

    def test_functor_composition_just(self):
        m = Just(5)

        left = m.fmap(lambda x: to_string(multiply_by_two(x)))
        right = m.fmap(multiply_by_two).fmap(to_string)

        assert left.value == right.value
        assert left.value == "10"

    def test_functor_composition_nothing(self):
        m = Nothing()

        left = m.fmap(lambda x: to_string(multiply_by_two(x)))
        right = m.fmap(multiply_by_two).fmap(to_string)

        assert isinstance(left, Nothing)
        assert isinstance(right, Nothing)


class TestApplicativeLaws:
    """
    Applicative laws:
    1. Identity: pure id <*> v = v
    2. Composition: pure (.) <*> u <*> v <*> w = u <*> (v <*> w)
    3. Homomorphism: pure f <*> pure x = pure (f x)
    4. Interchange: u <*> pure y = pure ($ y) <*> u
    """

    def test_applicative_identity_just(self):
        v = Just(42)
        result = v.ap(Maybe.pure(F.id))
        assert result == v

    def test_applicative_identity_nothing(self):
        v = Nothing()
        result = v.ap(Maybe.pure(F.id))
        assert isinstance(result, Nothing)

    def test_applicative_homomorphism(self):
        x = 10
        f = multiply_by_two

        left = Maybe.pure(x).ap(Maybe.pure(f))
        right = Maybe.pure(f(x))

        assert left == right
        assert isinstance(left, Just)
        assert left.value == 20

    def test_applicative_interchange_just(self):
        y = 5
        u = Just(multiply_by_two)

        left = Just(y).ap(u)
        right = u.ap(Maybe.pure(lambda f: f(y)))

        assert left == right
        assert isinstance(left, Just)
        assert left.value == 10

    def test_applicative_composition(self):
        u = Just(multiply_by_two)
        v = Just(add_one)
        w = Just(5)

        left = w.ap(v).ap(u)
        right = w.ap(v.ap(u.ap(Maybe.pure(F.compose))))

        assert left == right
        assert isinstance(left, Just)
        assert left.value == 12

    def test_applicative_nothing_function(self):
        v = Just(42)
        result = v.ap(Nothing())
        assert isinstance(result, Nothing)

    def test_applicative_nothing_value(self):
        f = Just(add_one)
        v = Nothing()
        result = v.ap(f)
        assert isinstance(result, Nothing)


class TestMonadLaws:
    """
    Monad laws:
    1. Left identity: pure a bind f = f a
    2. Right identity: m bind pure = m
    3. Associativity: (m bind f) bind g = m bind (lambda x: f x bind g)
    """

    def test_monad_left_identity(self):
        a = 5
        f = safe_divide

        left = Maybe.pure(a).bind(f)
        right = f(a)

        assert left == right
        assert isinstance(left, Just)
        assert left.value == 2.0

    def test_monad_left_identity_nothing_result(self):
        a = 0
        f = safe_divide

        left = Maybe.pure(a).bind(f)
        right = f(a)

        assert isinstance(left, Nothing)
        assert isinstance(right, Nothing)

    def test_monad_right_identity_just(self):
        m = Just(42)

        left = m.bind(Maybe.pure)
        right = m

        assert left == right

    def test_monad_right_identity_nothing(self):
        m = Nothing()

        left = m.bind(Maybe.pure)

        assert isinstance(left, Nothing)

    def test_monad_associativity(self):
        m = Just(4.0)
        f = safe_sqrt

        def g(x: float) -> Maybe[float]:
            return Just(x * 2)

        left = m.bind(f).bind(g)
        right = m.bind(lambda x: f(x).bind(g))

        assert left == right
        assert isinstance(left, Just)
        assert left.value == 4.0

    def test_monad_associativity_with_nothing(self):
        m = Just(-4.0)
        f = safe_sqrt

        def g(x: float) -> Maybe[float]:
            return Just(x * 2)

        left = m.bind(f).bind(g)
        right = m.bind(lambda x: f(x).bind(g))

        assert isinstance(left, Nothing)
        assert isinstance(right, Nothing)

    def test_monad_chain_operations(self):
        result = Just(2).bind(safe_divide).bind(safe_sqrt)
        assert isinstance(result, Just)
        assert isinstance(result.value, float)
        assert abs(result.value - 2.236067977) < 0.0001

    def test_monad_chain_with_nothing(self):
        result = Just(0).bind(safe_divide).bind(safe_sqrt)
        assert isinstance(result, Nothing)


class TestOperators:
    def test_pipe_operator_just(self):
        result = Just(5) | safe_divide
        assert isinstance(result, Just)
        assert result.value == 2.0

    def test_pipe_operator_nothing(self):
        result = Nothing() | safe_divide
        assert isinstance(result, Nothing)

    def test_xor_operator_just(self):
        result = Just(5) ** Just(multiply_by_two)
        assert isinstance(result, Just)
        assert result.value == 10

    def test_xor_operator_nothing_value(self):
        result = Nothing() ** Just(multiply_by_two)
        assert isinstance(result, Nothing)

    def test_xor_operator_nothing_function(self):
        result = Just(5) ** Nothing()
        assert isinstance(result, Nothing)

    def test_chained_pipe_operators(self):
        result = Just(4) | safe_divide | safe_sqrt
        assert isinstance(result, Just)
        assert isinstance(result.value, float)
        assert abs(result.value - 1.5811388) < 0.0001


class TestEdgeCases:
    def test_fmap_multiple_times(self):
        result = Just(1).fmap(add_one).fmap(multiply_by_two).fmap(add_one)
        assert result.value == 5

    def test_bind_returning_nothing(self):
        result = Just(0).bind(safe_divide)
        assert isinstance(result, Nothing)

    def test_nothing_propagation(self):
        result = Nothing().fmap(add_one).bind(safe_divide).fmap(multiply_by_two)
        assert isinstance(result, Nothing)

    def test_complex_chain(self):
        result: Maybe[float] = (
            Just(2)
            .fmap(multiply_by_two)
            .bind(safe_divide)
            .fmap(add_one)
            .bind(safe_sqrt)
        )
        assert isinstance(result, Just)
        assert isinstance(result.value, float)
        assert abs(result.value - 1.8708287) < 0.0001
