Type Hierarchy Reference
========================

Katharos organises its types into two independent abstract hierarchies defined in ``katharos.algebra``.

.. code-block:: none

    Combining             Computational
    ---------             -------------
    Semigroup[S]          Functor[F, A]
         |                     |
    Monoid[M]            Applicative[App, A]
                               |
                          Monad[Mon, A]

    Concrete types
    Maybe[A]         -> Monad
    Result[E, A]     -> Monad
    IO[A]            -> Monad
    ImmutableList[T] -> Monad + Monoid
    NonEmptyList[T]  -> Monad + Semigroup
    MonoidMaybe[A]   -> Monoid
    Sum              -> Monoid
    Product          -> Monoid

----

Combining Hierarchy
-------------------

``Semigroup[S]``
~~~~~~~~~~~~~~~~

**Module:** ``katharos.algebra.semigroup``

Abstract base class for types with an associative binary operation.

``op(other: S) -> S``
    Combines this value with *other*. Must satisfy ``(a @ b) @ c == a @ (b @ c)``.

    Exposed as the ``@`` operator: ``a @ b`` is equivalent to ``a.op(b)``.

----

``Monoid[M]``
~~~~~~~~~~~~~

**Module:** ``katharos.algebra.monoid``  |  **Extends:** ``Semigroup[M]``

Adds an identity element to ``Semigroup``.

``identity() -> M``  *(classmethod)*
    Returns the identity element. Must satisfy ``a @ identity() == a`` and
    ``identity() @ a == a`` for all ``a``.

----

Computational Hierarchy
-----------------------

``Functor[F, A]``
~~~~~~~~~~~~~~~~~

**Module:** ``katharos.algebra.functor``

Abstract base class for types that support mapping a function over their contents.

*Laws:* ``x.fmap(id) == x``  |  ``x.fmap(g ∘ f) == x.fmap(f).fmap(g)``

``fmap(f: Callable[[A], B]) -> Functor[F, B]``
    Applies *f* to the value inside the functor and returns a new functor of type ``B``.

----

``Applicative[App, A]``
~~~~~~~~~~~~~~~~~~~~~~~

**Module:** ``katharos.algebra.applicative``  |  **Extends:** ``Functor[App, A]``

Adds the ability to lift plain values into the context and to apply a wrapped function
to a wrapped value.

*Laws:*

- ``v ** App.pure(id) == v``
- ``App.pure(x) ** App.pure(f) == App.pure(f(x))``
- ``App.pure(y) ** u == u ** App.pure(lambda f: f(y))``
- ``w ** (v ** (u ** App.pure(compose))) == (w ** v) ** u``

``pure(x: T) -> Applicative[App, T]``  *(classmethod)*
    Lifts a plain value into the applicative context.

``ap(wrapped_funcs: Applicative[App, Callable[[A], B]]) -> Applicative[App, B]``
    Applies the function inside *wrapped_funcs* to the value inside this applicative.

    Exposed as the ``**`` operator: ``value ** wrapped_func`` is equivalent to
    ``value.ap(wrapped_func)``.

----

``Monad[Mon, A]``
~~~~~~~~~~~~~~~~~

**Module:** ``katharos.algebra.monad``  |  **Extends:** ``Applicative[Mon, A]``

Adds sequencing of computations that themselves produce monadic values.

*Laws:*

- ``Monad.ret(a).bind(f) == f(a)``
- ``m.bind(ret) == m``
- ``m.bind(f).bind(g) == m.bind(lambda x: f(x).bind(g))``

``ret(x: T) -> Monad[Mon, T]``  *(classmethod)*
    Lifts a plain value into the monad. Delegates to ``pure``.

``bind(f: Callable[[A], Monad[Mon, B]]) -> Monad[Mon, B]``  *(abstract)*
    Passes the unwrapped value to *f* and returns the resulting monad.
    Short-circuits on failure contexts (``Nothing``, ``Failure``).

    Exposed as the ``|`` operator: ``m | f`` is equivalent to ``m.bind(f)``.

``then(other: Monad[Mon, B]) -> Monad[Mon, B]``
    Sequences two monadic actions, discarding the value of the first.

    Exposed as the ``>>`` operator: ``m1 >> m2`` is equivalent to ``m1.then(m2)``.

----

Concrete Types
--------------

.. list-table::
   :header-rows: 1
   :widths: 22 28 50

   * - Type
     - Implements
     - Notes
   * - ``Maybe[A]``
     - ``Monad``
     - States: ``Just(value)`` / ``Nothing()``. ``@final`` — do not subclass.
   * - ``Result[E, A]``
     - ``Monad``
     - States: ``Success(value)`` / ``Failure(exc)``. ``@final`` — do not subclass.
   * - ``IO[A]``
     - ``Monad``
     - Lazy side-effect wrapper. Call ``.execute()`` to run the wrapped action.
   * - ``ImmutableList[T]``
     - ``Monad``, ``Monoid``
     - Immutable sequence wrapping a Python list.
   * - ``NonEmptyList[T]``
     - ``Monad``, ``Semigroup``
     - Guaranteed non-empty. Exposes ``.head`` and ``.tail``.
   * - ``MonoidMaybe[A]``
     - ``Monoid``
     - ``Maybe`` with a ``Monoid`` instance. Requires the wrapped type to be a ``Semigroup``.
   * - ``Sum``
     - ``Monoid``
     - Numeric monoid under addition. Identity: ``0``.
   * - ``Product``
     - ``Monoid``
     - Numeric monoid under multiplication. Identity: ``1``.
