"""Static API checks.

Run with: uv run pyright src tests/types/either/typecheck_either.py
"""

# pyright: reportUnnecessaryTypeIgnoreComment=true

from collections.abc import Callable
from typing import Never, assert_type

from katharos.types import Either


def check_construction() -> None:
    assert_type(Either.Left("error"), Either[str, Never])
    assert_type(Either.Right(1), Either[Never, int])
    assert_type(Either.Left(None), Either[None, Never])
    assert_type(Either.Right(None), Either[Never, None])
    assert_type(Either.pure(1), Either[Never, int])
    assert_type(Either.ret(1), Either[Never, int])
    assert_type(Either[str, int].Left("error"), Either[str, int])
    assert_type(Either[str, int].Right(1), Either[str, int])
    assert_type(Either[str, int].pure("new type"), Either[str, str])
    assert_type(Either[str, int].ret(None), Either[str, None])
    Either[str, int].Left(1)  # pyright: ignore[reportArgumentType]
    Either[str, int].Right("wrong")  # pyright: ignore[reportArgumentType]


def check_covariance(value: Either[ValueError, int]) -> Either[BaseException, object]:
    return value


def stringify(value: int) -> str:
    return str(value)


def check_operations(
    value: Either[str, int],
    function: Either[ValueError, Callable[[int], str]],
    continuation: Callable[[int], Either[ValueError, str]],
    other: Either[ValueError, str],
) -> None:
    assert_type(value.left, str)
    assert_type(value.right, int)
    assert_type(value.unwrap(), int)
    assert_type(value.fmap(stringify), Either[str, str])
    assert_type(value.bind(continuation), Either[str | ValueError, str])
    assert_type(value | continuation, Either[str | ValueError, str])
    assert_type(value.ap(function), Either[str | ValueError, str])
    assert_type(value**function, Either[str | ValueError, str])
    assert_type(value.then(other), Either[str | ValueError, str])
    assert_type(value >> other, Either[str | ValueError, str])
    assert_type(value.map_left(len), Either[int, int])
    assert_type(value.bimap(len, stringify), Either[int, str])
    assert_type(value.either(len, lambda x: x * 2), int)


def check_bare_chaining() -> None:
    assert_type(Either.Right(1).fmap(stringify), Either[Never, str])
    assert_type(Either.Right(1).bind(Either.Right), Either[Never, int])
    assert_type(Either.Right(1) | Either.Right, Either[Never, int])
    assert_type(Either.Right(1) ** Either.Right(stringify), Either[Never, str])
    assert_type(Either.Right(1) >> Either.Right("done"), Either[Never, str])
