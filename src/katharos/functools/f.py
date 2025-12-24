from collections.abc import Callable


class F:
    """
    This class serves as a namespace for utility functions.
    All functions are static and can be called without instantiating the class.
    """

    @staticmethod
    def compose[A, B, C](
        f: Callable[[B], C],
    ) -> Callable[[Callable[[A], B]], Callable[[A], C]]:
        """
        Compose two functions.

        Args:
            f: A function from B to C

        Returns:
            A function that takes a function from A to B and returns a function from A to C
        """

        def inner(g: Callable[[A], B]) -> Callable[[A], C]:
            return lambda x: f(g(x))

        return inner

    @staticmethod
    def id[A](x: A) -> A:
        """
        Identity function.

        Args:
            x: Input value

        Returns:
            The same value x
        """
        return x
