class UnwrapError(Exception):
    """Raised when extracting a value that is absent.

    Covers unwrapping a Nothing :class:`~katharos.types.Maybe`, getting the
    value of a Failure :class:`~katharos.types.Result`, or getting the error
    of a Success :class:`~katharos.types.Result`.
    """
