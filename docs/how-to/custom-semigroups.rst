How to Implement a Custom Semigroup and Monoid
===============================================

This guide shows you how to create your own types that plug into Katharos' algebraic hierarchy by implementing ``Semigroup`` and ``Monoid``.

Prerequisites
-------------

- ``katharos`` installed
- Familiarity with the ``@`` operator (semigroup combine) and the built-in ``Sum`` / ``Product`` types as reference

Implementing a Semigroup
-------------------------

Subclass ``Semigroup`` and implement the ``op`` method. The operation must be **associative**: ``(a @ b) @ c == a @ (b @ c)`` for all values.

.. code-block:: python

   from katharos.algebra import Semigroup

   class MaxInt(Semigroup["MaxInt"]):
       """Semigroup that combines by taking the maximum."""

       def __init__(self, value: int) -> None:
           self.value = value

       def op(self, other: "MaxInt") -> "MaxInt":
           return MaxInt(max(self.value, other.value))

       def __repr__(self) -> str:
           return f"MaxInt({self.value})"

The ``@`` operator is provided by the base class and delegates to ``op``:

.. code-block:: python

   a = MaxInt(3)
   b = MaxInt(7)
   c = MaxInt(5)

   print(a @ b)        # MaxInt(7)
   print(a @ b @ c)    # MaxInt(7)  — associativity holds

Using your semigroup with F.sigma
----------------------------------

``F.sigma`` folds a ``NonEmptyList`` of semigroup values using ``@``. Your type works immediately:

.. code-block:: python

   from katharos.functools import F
   from katharos.types.list import NonEmptyList

   values = NonEmptyList(MaxInt(3), [MaxInt(7), MaxInt(1), MaxInt(9), MaxInt(2)])
   print(F.sigma(values))  # MaxInt(9)

Upgrading to a Monoid
-----------------------

A ``Monoid`` is a ``Semigroup`` with an identity element: a value ``e`` such that ``e @ a == a`` and ``a @ e == a`` for all ``a``. Add a ``@classmethod`` named ``identity``:

.. code-block:: python

   from katharos.algebra import Monoid

   class MaxInt(Monoid["MaxInt"]):
       """Monoid that combines by taking the maximum, with identity -infinity."""

       def __init__(self, value: int) -> None:
           self.value = value

       def op(self, other: "MaxInt") -> "MaxInt":
           return MaxInt(max(self.value, other.value))

       @classmethod
       def identity(cls) -> "MaxInt":
           return MaxInt(-(2 ** 63))   # acts as -∞ for any practical int

       def __repr__(self) -> str:
           return f"MaxInt({self.value})"

Verify the identity laws:

.. code-block:: python

   e = MaxInt.identity()
   x = MaxInt(42)

   assert (e @ x) == x
   assert (x @ e) == x

Using your monoid with foldl
-----------------------------

With an identity element you can fold over an empty sequence safely using ``F.foldl``:

.. code-block:: python

   from katharos.functools import F
   from operator import matmul

   values = [MaxInt(3), MaxInt(7), MaxInt(1)]
   result = F.foldl(matmul, MaxInt.identity(), values)
   print(result)  # MaxInt(7)

   empty_result = F.foldl(matmul, MaxInt.identity(), [])
   print(empty_result)  # MaxInt(-9223372036854775808)  — the identity

Example: a string-joining semigroup
-------------------------------------

.. code-block:: python

   from katharos.algebra import Monoid

   class JoinedStr(Monoid["JoinedStr"]):
       """Monoid over strings, joining with a comma separator."""

       def __init__(self, value: str) -> None:
           self.value = value

       def op(self, other: "JoinedStr") -> "JoinedStr":
           if not self.value:
               return other
           if not other.value:
               return self
           return JoinedStr(f"{self.value}, {other.value}")

       @classmethod
       def identity(cls) -> "JoinedStr":
           return JoinedStr("")

       def __repr__(self) -> str:
           return f'JoinedStr("{self.value}")'

   parts = [JoinedStr("alice"), JoinedStr("bob"), JoinedStr("carol")]
   result = F.foldl(matmul, JoinedStr.identity(), parts)
   print(result)  # JoinedStr("alice, bob, carol")
