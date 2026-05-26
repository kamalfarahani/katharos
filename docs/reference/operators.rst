Operator Reference
==================

Katharos exposes algebraic operations as Python operators. This page documents each operator, its syntax, and the method it delegates to.

----

``fmap`` — Functor map
-----------------------

**Syntax:** ``functor.fmap(f)``

**Delegates to:** ``Functor.fmap``

Applies *f* to the value inside the functor. Returns a new functor of the same shape.

.. code-block:: python

   from katharos.types import Maybe

   Maybe[int].Just(5).fmap(lambda x: x * 2)   # Just(10)
   Maybe[int].Nothing().fmap(lambda x: x * 2) # Nothing()

----

``**`` — Applicative apply
---------------------------

**Syntax:** ``value ** wrapped_func``

**Delegates to:** ``Applicative.ap``

Applies the function inside *wrapped_func* to the value inside *value*.

.. code-block:: python

   from katharos.types import Maybe

   add = lambda x: lambda y: x + y

   Maybe[int].Just(3) ** Maybe[int].Just(add(5))    # Just(8)
   Maybe[int].Nothing() ** Maybe[int].Just(add(5))  # Nothing()

----

``|`` — Monadic bind
---------------------

**Syntax:** ``monad | f``

**Delegates to:** ``Monad.bind``

Passes the unwrapped value to *f* and returns the resulting monad.
Short-circuits on ``Nothing`` or ``Failure`` — *f* is not called.

.. code-block:: python

   from katharos.types import Maybe

   def lookup_role(uid: int) -> Maybe[str]:
       roles = {1: "admin", 2: "viewer"}
       r = roles.get(uid)
       return Maybe[str].Just(r) if r is not None else Maybe[str].Nothing()

   Maybe[int].Just(1) | lookup_role   # Just('admin')
   Maybe[int].Just(9) | lookup_role   # Nothing()
   Maybe[int].Nothing() | lookup_role # Nothing()

----

``>>`` — Sequence
------------------

**Syntax:** ``monad1 >> monad2``

**Delegates to:** ``Monad.then``

Sequences two monadic actions. The value of *monad1* is discarded; the result is *monad2*.

.. code-block:: python

   from katharos.types import Maybe

   Maybe[int].Just(5) >> Maybe[str].Just("ok")  # Just('ok')
   Maybe[int].Nothing() >> Maybe[str].Just("ok") # Nothing()

----

``@`` — Semigroup combine
--------------------------

**Syntax:** ``a @ b``

**Delegates to:** ``Semigroup.op``

Combines two semigroup values. Must satisfy associativity:
``(a @ b) @ c == a @ (b @ c)``.

.. code-block:: python

   from katharos.types import NonEmptyList

   NonEmptyList(1, [2, 3]) @ NonEmptyList(4, [5, 6])
   # NonEmptyList(1, [2, 3, 4, 5, 6])

----

Operator Precedence
-------------------

Python's built-in precedence applies. From highest to lowest:

======  =======================
``**``  Applicative apply
``@``   Semigroup combine
``>>``  Sequence
``|``   Monadic bind (lowest)
======  =======================

Use parentheses when mixing operators to make evaluation order explicit.

----

Operators by Type
-----------------

===================  =====================================
Type                 Operators
===================  =====================================
``Maybe[A]``         ``fmap``, ``|``, ``**``, ``>>``
``Result[E, A]``     ``fmap``, ``|``, ``**``, ``>>``
``IO[A]``            ``fmap``, ``|``, ``**``, ``>>``
``ImmutableList[T]`` ``fmap``, ``|``, ``**``, ``>>`` ``+``, ``@``
``NonEmptyList[T]``  ``fmap``, ``|``, ``**``, ``>>`` ``@``
``Sum``              ``@``
``Product``          ``@``
``MonoidMaybe[A]``   ``@``
===================  =====================================
