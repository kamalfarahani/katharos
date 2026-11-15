from __future__ import annotations

from collections.abc import Callable
from typing import Any, Generic, Never, TypeVar, cast, final, overload

from katharos.algebra import Applicative, Monad
from katharos.types.errors import UnwrapError

L_co = TypeVar("L_co", covariant=True)
R_co = TypeVar("R_co", covariant=True)


@final
class Either(
    Monad["Either[L_co, Any]", R_co],
    Generic[L_co, R_co],  # noqa: UP046 - Preserve explicit covariance.
):
    """A right-biased choice between two arbitrary payload types.

    Construct values with :meth:`Left` or :meth:`Right`. Both branches accept
    any value, including ``None`` and exceptions. The branch is tracked
    independently of the payload. Direct construction raises :class:`TypeError`.

    :meth:`fmap`, :meth:`bind`, and :meth:`ap` operate on Right values and
    short-circuit on Left. Use :meth:`map_left` or :meth:`bimap` to transform
    the Left branch, and :meth:`either` to handle both branches. Exceptions
    raised by callbacks propagate unchanged.

    Note:
        This class is ``@final``. Check the branch with :meth:`is_left` and
        :meth:`is_right`, and extract its payload with :attr:`left` or
        :attr:`right`. Truthiness reflects the branch: Right is always truthy
        and Left is always falsy, regardless of the payload.

        Like :class:`~katharos.types.Result`, :meth:`ap` takes the wrapped
        function as its argument. If both operands are Left, the receiver
        wins. Haskell's ``<*>`` instead gives the function operand precedence.

    Examples:
        >>> from katharos.types import Either
        >>> Either.Right(3).fmap(lambda x: x * 2)
        Right(6)
        >>> Either.Left("invalid").fmap(lambda x: x * 2)
        Left('invalid')
        >>> Either.Right(3) | (lambda x: Either.Right(x + 1))
        Right(4)
        >>> Either.Right(None).right is None
        True
        >>> Either.Left(None).left is None
        True
        >>> Either.Left("invalid").either(str.upper, str)
        'INVALID'
    """

    _value: L_co | R_co
    _is_right: bool

    def __init__(self) -> None:
        """Reject direct construction; use :meth:`Left` or :meth:`Right`.

        Raises:
            TypeError: Always, because a branch must be chosen explicitly.
        """
        raise TypeError("Use Either.Left() or Either.Right() to construct an Either")

    @classmethod
    def _create(
        cls: type[Either[Any, Any]], value: Any, *, is_right: bool
    ) -> Either[Any, Any]:
        instance = object.__new__(cls)
        instance._value = value
        instance._is_right = is_right
        return instance

    # As in Result, the first overload infers the absent branch as Never for
    # bare factory calls; the second enforces both specialized class arguments.
    @overload
    @classmethod
    def Left[L](cls: type[Either[Never, Never]], value: L) -> Either[L, Never]: ...

    @overload
    @classmethod
    def Left[L, R](cls: type[Either[L, R]], value: L) -> Either[L, R]: ...

    @classmethod
    def Left(cls: type[Either[Any, Any]], value: Any) -> Either[Any, Any]:
        """Create a Left containing the given value.

        Args:
            value: The Left payload, with no restriction on its type.

        Returns:
            A Left containing the value.

        Examples:
            >>> Either.Left("invalid")
            Left('invalid')
            >>> Either[str, int].Left("invalid")
            Left('invalid')
        """
        return cls._create(value, is_right=False)

    @overload
    @classmethod
    def Right[R](cls: type[Either[Never, Never]], value: R) -> Either[Never, R]: ...

    @overload
    @classmethod
    def Right[L, R](cls: type[Either[L, R]], value: R) -> Either[L, R]: ...

    @classmethod
    def Right(cls: type[Either[Any, Any]], value: Any) -> Either[Any, Any]:
        """Create a Right containing the given value.

        Args:
            value: The Right payload, with no restriction on its type.

        Returns:
            A Right containing the value.

        Examples:
            >>> Either.Right(42)
            Right(42)
            >>> Either[str, int].Right(42)
            Right(42)
        """
        return cls._create(value, is_right=True)

    @overload
    @classmethod
    def pure[T](cls: type[Either[Never, Never]], x: T) -> Either[Never, T]: ...

    @overload
    @classmethod
    def pure[L, T](cls: type[Either[L, Any]], x: T) -> Either[L, T]: ...

    @classmethod
    def pure(cls: type[Either[Any, Any]], x: Any) -> Either[Any, Any]:
        """Lift a value into Right, preserving a specialized Left type.

        Args:
            x: The value to wrap.

        Returns:
            A Right containing the value.

        Examples:
            >>> Either.pure(ValueError("data"))
            Right(ValueError('data'))
        """
        return cls.Right(x)

    @overload
    @classmethod
    def ret[T](cls: type[Either[Never, Never]], x: T) -> Either[Never, T]: ...

    @overload
    @classmethod
    def ret[L, T](cls: type[Either[L, Any]], x: T) -> Either[L, T]: ...

    @classmethod
    def ret(cls: type[Either[Any, Any]], x: Any) -> Either[Any, Any]:
        """Lift a value into Right, as an alias for :meth:`pure`.

        Args:
            x: The value to wrap.

        Returns:
            A Right containing the value.
        """
        return cls.pure(x)

    @property
    def left(self) -> L_co:
        """Extract the Left payload.

        Returns:
            The value contained in Left.

        Raises:
            UnwrapError: If this is a Right.
        """
        if self._is_right:
            raise UnwrapError("Cannot get the left value of a Right")
        return cast(L_co, self._value)

    @property
    def right(self) -> R_co:
        """Extract the Right payload.

        Returns:
            The value contained in Right.

        Raises:
            UnwrapError: If this is a Left.
        """
        if not self._is_right:
            raise UnwrapError("Cannot get the right value of a Left")
        return cast(R_co, self._value)

    def unwrap(self) -> R_co:
        """Extract the Right payload, as an alias for :attr:`right`.

        Returns:
            The value contained in Right.

        Raises:
            UnwrapError: If this is a Left.
        """
        return self.right

    def is_left(self) -> bool:
        """Return whether this is a Left."""
        return not self._is_right

    def is_right(self) -> bool:
        """Return whether this is a Right."""
        return self._is_right

    def fmap[B](self, f: Callable[[R_co], B]) -> Either[L_co, B]:
        """Map a function over Right, preserving Left unchanged.

        Args:
            f: The function to apply to a Right payload.

        Returns:
            A Right containing the mapped value, or the original Left.
        """
        if self.is_left():
            return cast(Either[L_co, B], self)
        return Either.Right(f(self.right))

    def ap[L2, B](
        self,
        wrapped_funcs: Applicative[Either[L2, Any], Callable[[R_co], B]],
    ) -> Either[L_co | L2, B]:
        """Apply a wrapped function, giving a receiver Left precedence.

        Args:
            wrapped_funcs: An Either containing the function to apply.

        Returns:
            The receiver if it is Left, otherwise the function's Left or a
            Right containing the applied result.

        Examples:
            >>> Either.Right(3) ** Either.Right(lambda x: x + 1)
            Right(4)
            >>> Either.Left("value") ** Either.Left("function")
            Left('value')
        """
        if self.is_left():
            return cast(Either[L_co | L2, B], self)
        functions = cast(Either[L2, Callable[[R_co], B]], wrapped_funcs)
        if functions.is_left():
            return cast(Either[L_co | L2, B], functions)
        return Either.Right(functions.right(self.right))

    def bind[L2, B](
        self, f: Callable[[R_co], Monad[Either[L2, Any], B]]
    ) -> Either[L_co | L2, B]:
        """Chain an Either-returning function on Right.

        Args:
            f: A function taking the Right payload and returning an Either.

        Returns:
            The original Left, or the Either returned by the function.
        """
        if self.is_left():
            return cast(Either[L_co | L2, B], self)
        return cast(Either[L2, B], f(self.right))

    def then[L2, B](self, other: Monad[Either[L2, Any], B]) -> Either[L_co | L2, B]:
        """Sequence two Eithers, discarding the receiver's Right payload.

        Args:
            other: The Either to return if the receiver is Right.

        Returns:
            The original Left, or the second Either.

        Examples:
            >>> Either.Right(1) >> Either.Right("done")
            Right('done')
            >>> Either.Left("stop") >> Either.Right("done")
            Left('stop')
        """
        return self.bind(lambda _: other)

    def map_left[B](self, f: Callable[[L_co], B]) -> Either[B, R_co]:
        """Map a function over Left, preserving Right unchanged.

        Args:
            f: The function to apply to a Left payload.

        Returns:
            A Left containing the mapped value, or the original Right.

        Examples:
            >>> Either.Left("invalid").map_left(str.upper)
            Left('INVALID')
        """
        if self.is_right():
            return cast(Either[B, R_co], self)
        return Either.Left(f(self.left))

    def bimap[A, B](
        self, on_left: Callable[[L_co], A], on_right: Callable[[R_co], B]
    ) -> Either[A, B]:
        """Transform the active branch, preserving its side.

        Args:
            on_left: The function to apply to a Left payload.
            on_right: The function to apply to a Right payload.

        Returns:
            An Either containing the active branch's mapped value.

        Examples:
            >>> Either.Right(3).bimap(str.upper, lambda x: x * 2)
            Right(6)
        """
        if self.is_left():
            return Either.Left(on_left(self.left))
        return Either.Right(on_right(self.right))

    def either[C](
        self, on_left: Callable[[L_co], C], on_right: Callable[[R_co], C]
    ) -> C:
        """Handle the active branch and return its handler's plain result.

        Args:
            on_left: The handler for a Left payload.
            on_right: The handler for a Right payload.

        Returns:
            The result of the active branch's handler.
        """
        if self.is_left():
            return on_left(self.left)
        return on_right(self.right)

    def __or__[L2, B](
        self, f: Callable[[R_co], Monad[Either[L2, Any], B]]
    ) -> Either[L_co | L2, B]:
        """Delegate the ``|`` operator to :meth:`bind`."""
        return self.bind(f)

    def __pow__[L2, B](
        self,
        wrapped_funcs: Applicative[Either[L2, Any], Callable[[R_co], B]],
    ) -> Either[L_co | L2, B]:
        """Delegate the ``**`` operator to :meth:`ap`."""
        return self.ap(wrapped_funcs)

    def __rshift__[L2, B](
        self, other: Monad[Either[L2, Any], B]
    ) -> Either[L_co | L2, B]:
        """Delegate the ``>>`` operator to :meth:`then`."""
        return self.then(other)

    def __repr__(self) -> str:
        """Return ``Left(<payload>)`` or ``Right(<payload>)``."""
        branch = "Right" if self._is_right else "Left"
        return f"{branch}({self._value!r})"

    def __eq__(self, value: object, /) -> bool:
        """Compare the branch and payload, deferring foreign comparisons."""
        if not isinstance(value, Either):
            return NotImplemented
        return self._is_right == value._is_right and self._value == value._value

    def __hash__(self) -> int:
        """Hash the branch and payload; unhashable payloads raise TypeError."""
        return hash((self._is_right, self._value))

    def __bool__(self) -> bool:
        """Return True for Right and False for Left, regardless of payload."""
        return self._is_right
