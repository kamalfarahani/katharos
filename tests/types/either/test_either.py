from typing import Never

import pytest

from katharos.algebra import Monad
from katharos.functools import F
from katharos.syntax_sugar import DoBlock, do
from katharos.types import Either, UnwrapError
from katharos.types.either import Either as ModuleEither


def unexpected(_: object) -> Never:
    pytest.fail("Inactive branch callback was called")


class TestConstruction:
    def test_public_export(self):
        assert Either is ModuleEither
        assert isinstance(Either.Right(1), Monad)

    @pytest.mark.parametrize(
        "value", [None, 0, False, "", [], {"field": "invalid"}, ValueError("data")]
    )
    def test_arbitrary_payloads(self, value):
        left = Either.Left(value)
        right = Either.Right(value)
        assert left.is_left() and not left.is_right()
        assert right.is_right() and not right.is_left()
        assert left.left is value
        assert right.right is value
        assert right.unwrap() is value
        assert not left
        assert bool(right)
        assert left != right
        assert repr(left) == f"Left({value!r})"
        assert repr(right) == f"Right({value!r})"

    @pytest.mark.parametrize("factory", [Either.pure, Either.ret])
    def test_lifting_always_creates_right(self, factory):
        for value in [None, ValueError("data"), Either.Left("nested")]:
            lifted = factory(value)
            assert lifted.is_right()
            assert lifted.right is value

    def test_specialized_factories(self):
        assert Either[str, int].Left("invalid") == Either.Left("invalid")
        assert Either[str, int].Right(42) == Either.Right(42)
        assert Either[str, int].pure("new type") == Either.Right("new type")
        assert Either[str, int].ret(None) == Either.Right(None)

    @pytest.mark.parametrize("outer", [Either.Left, Either.Right])
    @pytest.mark.parametrize("inner", [Either.Left(None), Either.Right(None)])
    def test_nested_payload_preserves_both_branches(self, outer, inner):
        wrapped = outer(inner)
        assert wrapped.either(F.id, F.id) is inner

    def test_direct_construction_requires_factory(self):
        with pytest.raises(TypeError, match=r"Either.Left\(\).*Either.Right\(\)"):
            Either()

    @pytest.mark.parametrize(
        "kwargs", [{"left": None}, {"right": None}, {"left": 1, "right": 2}]
    )
    def test_direct_keyword_construction_is_rejected(self, kwargs):
        with pytest.raises(TypeError):
            Either(**kwargs)

    def test_direct_positional_construction_is_rejected(self):
        with pytest.raises(TypeError):
            Either(42)


class TestAccessors:
    def test_left_on_right_raises(self):
        with pytest.raises(UnwrapError, match="Cannot get the left value of a Right"):
            _ = Either.Right(None).left

    def test_right_on_left_raises(self):
        with pytest.raises(UnwrapError, match="Cannot get the right value of a Left"):
            _ = Either.Left(None).right

    def test_unwrap_on_left_raises(self):
        with pytest.raises(UnwrapError, match="Cannot get the right value of a Left"):
            Either.Left("invalid").unwrap()

    @pytest.mark.parametrize("name", ["left", "right"])
    def test_branch_accessors_are_read_only(self, name):
        with pytest.raises(AttributeError):
            setattr(Either.Right(1), name, 2)


class TestComposition:
    def test_successful_chain(self):
        result = (
            Either.Right("21").fmap(int).bind(lambda x: Either.Right(x * 2)).fmap(str)
        )
        assert result == Either.Right("42")

    def test_left_short_circuits_fmap_and_bind(self):
        original = Either.Left({"reason": "invalid"})
        assert original.fmap(unexpected) is original
        assert original.bind(unexpected) is original
        assert (original | unexpected) is original

    def test_bind_can_produce_left(self):
        left = Either.Left("invalid")
        result = Either.Right(42).bind(lambda _: left)
        assert result is left
        assert result.fmap(unexpected) is left

    def test_bind_flattens_one_layer(self):
        inner = Either.Left("nested")
        assert Either.Right(inner).bind(F.id) is inner

    @pytest.mark.parametrize("receiver", [Either.Left("first"), Either.Right(1)])
    @pytest.mark.parametrize("other", [Either.Left("second"), Either.Right("done")])
    def test_sequencing(self, receiver, other):
        expected = receiver if receiver.is_left() else other
        assert receiver.then(other) is expected
        assert (receiver >> other) is expected

    def test_applicative_application(self):
        value = Either.Right(21)
        function = Either.Right(lambda x: x * 2)
        assert value.ap(function) == Either.Right(42)
        assert value**function == Either.Right(42)

    def test_applicative_left_in_value(self):
        left = Either.Left("value")
        assert left.ap(Either.Right(unexpected)) is left

    def test_applicative_left_in_function(self):
        left = Either.Left("function")
        assert Either.Right(21).ap(left) is left

    def test_receiver_left_wins_when_both_are_left(self):
        left = Either.Left("value")
        assert left.ap(Either.Left("function")) is left


class TestBranchTools:
    def test_map_left(self):
        assert Either.Left("invalid").map_left(str.upper) == Either.Left("INVALID")
        right = Either.Right(None)
        assert right.map_left(unexpected) is right

    def test_bimap_calls_only_active_branch(self):
        assert Either.Left("invalid").bimap(len, unexpected) == Either.Left(7)
        assert Either.Right(21).bimap(unexpected, str) == Either.Right("21")

    def test_either_returns_plain_result_of_active_handler(self):
        assert Either.Left("invalid").either(len, unexpected) == 7
        assert Either.Right(None).either(unexpected, F.id) is None

    @pytest.mark.parametrize(
        "operation",
        [
            lambda f: Either.Right(1).fmap(f),
            lambda f: Either.Right(1).bind(f),
            lambda f: Either.Right(1).ap(Either.Right(f)),
            lambda f: Either.Left(1).map_left(f),
            lambda f: Either.Left(1).bimap(f, unexpected),
            lambda f: Either.Right(1).bimap(unexpected, f),
            lambda f: Either.Left(1).either(f, unexpected),
            lambda f: Either.Right(1).either(unexpected, f),
        ],
    )
    def test_callback_exceptions_propagate(self, operation):
        error = ValueError("callback failed")

        def fail(_: object) -> Never:
            raise error

        with pytest.raises(ValueError) as exc:
            operation(fail)
        assert exc.value is error


class TestEqualityAndHash:
    @pytest.mark.parametrize("factory", [Either.Left, Either.Right])
    def test_payload_equality(self, factory):
        assert factory([1, 2]) == factory([1, 2])
        assert factory(1) != factory(2)
        assert factory(1) == factory(True)
        assert hash(factory(1)) == hash(factory(True))
        with pytest.raises(TypeError):
            hash(factory([]))

    def test_branch_is_part_of_equality_and_hash(self):
        left, right = Either.Left(1), Either.Right(1)
        assert left != right
        assert len({left, right}) == 2

    def test_foreign_comparisons(self):
        left, right = Either.Left(1), Either.Right(1)
        assert left != 1
        assert right != 1
        assert left.__eq__(object()) is NotImplemented
        assert right.__eq__(object()) is NotImplemented

    def test_foreign_reflected_equality(self):
        class AlwaysEqual:
            def __eq__(self, other: object) -> bool:
                return True

        assert Either.Left(1) == AlwaysEqual()
        assert Either.Right(1) == AlwaysEqual()
        assert AlwaysEqual() == Either.Left(1)


class TestIntegration:
    def test_do_lifts_return_value(self):
        @do(Either)
        def computation() -> DoBlock[Either, int]:
            x: int = yield Either.Right(20)
            y: int = yield Either.Right(22)
            return x + y

        assert computation() == Either.Right(42)

    @pytest.mark.parametrize("index", [0, 1])
    def test_do_short_circuits_on_left(self, index):
        left = Either.Left("invalid")
        values = [Either.Right(1), Either.Right(2)]
        values[index] = left
        reached_return = False

        @do(Either)
        def computation() -> DoBlock[Either, int]:
            nonlocal reached_return
            x: int = yield values[0]
            y: int = yield values[1]
            reached_return = True
            return x + y

        assert computation() is left
        assert not reached_return

    def test_lift_a2_and_lift_a3(self):
        assert F.lift_a2(
            lambda x, y: x + y, Either.Right(20), Either.Right(22)
        ) == Either.Right(42)
        assert F.lift_a3(
            lambda x, y, z: x + y + z,
            Either.Right(10),
            Either.Right(20),
            Either.Right(12),
        ) == Either.Right(42)

    @pytest.mark.parametrize("index", [0, 1, 2])
    def test_lifting_short_circuits_on_left(self, index):
        left = Either.Left("invalid")
        values = [Either.Right(1), Either.Right(2), Either.Right(3)]
        values[index] = left
        assert F.lift_a3(lambda x, y, z: x + y + z, *values) is left
        if index < 2:
            assert F.lift_a2(lambda x, y: x + y, *values[:2]) is left
