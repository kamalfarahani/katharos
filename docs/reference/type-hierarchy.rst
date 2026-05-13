Type Hierarchy
==============

This page documents the hierarchy of algebraic abstractions in Katharos and which types implement which abstractions.

Abstraction Hierarchy
---------------------

Katharos follows a clear hierarchy of algebraic abstractions, where each level builds upon the previous:

.. code-block:: text

   Semigroup
       ↓
   Monoid
       ↓
   Functor
       ↓
   Applicative
       ↓
   Monad

Each abstraction adds more structure and capabilities:

- **Semigroup**: Associative binary operation (``@``)
- **Monoid**: Semigroup + identity element
- **Functor**: Can map functions over the structure (``fmap``)
- **Applicative**: Functor + function application (``pure``, ``ap``)
- **Monad**: Applicative + sequencing (``bind``, ``ret``)

Implementation Matrix
---------------------

This table shows which types implement which abstractions:

.. list-table::
   :header-rows: 1
   :widths: 30 15 15 15 15 15

   * - Type
     - Semigroup
     - Monoid
     - Functor
     - Applicative
     - Monad
   * - Maybe
     - ❌
     - ❌
     - ✅
     - ✅
     - ✅
   * - MonoidMaybe
     - ✅
     - ✅
     - ✅
     - ✅
     - ✅
   * - Result
     - ❌
     - ❌
     - ✅
     - ✅
     - ✅
   * - ImmutableList
     - ✅
     - ✅
     - ✅
     - ✅
     - ✅
   * - NonEmptyList
     - ✅
     - ❌
     - ✅
     - ✅
     - ✅
   * - IO
     - ❌
     - ❌
     - ✅
     - ✅
     - ✅

Type Details
------------

Maybe
~~~~~

:Implements: Functor, Applicative, Monad
:Purpose: Optional values without None checks
:Operations: ``fmap``, ``pure``, ``ap``, ``bind``
:Operators: ``|`` (bind), ``**`` (ap)

.. code-block:: python

   from katharos.types import Maybe
   
   # Functor
   Maybe.Just(5).fmap(lambda x: x * 2)  # Just(10)
   
   # Applicative
   Maybe.Just(5) ** Maybe.Just(lambda x: x * 2)  # Just(10)
   
   # Monad
   Maybe.Just(5) | (lambda x: Maybe.Just(x * 2))  # Just(10)

MonoidMaybe
~~~~~~~~~~~

:Implements: Semigroup, Monoid, Functor, Applicative, Monad
:Purpose: Maybe with monoid operations
:Operations: ``op``, ``identity``, ``fmap``, ``pure``, ``ap``, ``bind``
:Operators: ``@`` (op), ``|`` (bind), ``**`` (ap)

Result
~~~~~~

:Implements: Functor, Applicative, Monad
:Purpose: Error handling without exceptions
:Operations: ``fmap``, ``pure``, ``ap``, ``bind``
:Operators: ``|`` (bind), ``**`` (ap)

.. code-block:: python

   from katharos.types import Result
   
   # Success case
   Result.Success(5).fmap(lambda x: x * 2)  # Success(10)
   
   # Failure case
   Result.Failure(ValueError("error")).fmap(lambda x: x * 2)
   # Failure(ValueError('error'))

ImmutableList
~~~~~~~~~~~~~

:Implements: Semigroup, Monoid, Functor, Applicative, Monad
:Purpose: Immutable list with full algebraic operations
:Operations: ``op``, ``identity``, ``fmap``, ``pure``, ``ap``, ``bind``
:Operators: ``@`` (op), ``+`` (concat), ``|`` (bind), ``**`` (ap)

.. code-block:: python

   from katharos.types import ImmutableList
   
   # Semigroup
   ImmutableList([1, 2]) @ ImmutableList([3, 4])
   # ImmutableList([1, 2, 3, 4])
   
   # Monoid
   ImmutableList.identity()  # ImmutableList([])
   
   # Monad
   ImmutableList([1, 2, 3]) | (lambda x: ImmutableList([x, x * 2]))
   # ImmutableList([1, 2, 2, 4, 3, 6])

NonEmptyList
~~~~~~~~~~~~

:Implements: Semigroup, Functor, Applicative, Monad
:Purpose: List guaranteed to have at least one element
:Operations: ``op``, ``fmap``, ``pure``, ``ap``, ``bind``
:Operators: ``@`` (op), ``|`` (bind), ``**`` (ap)

Note: NonEmptyList is a Semigroup but not a Monoid (no identity element).

IO
~~

:Implements: Functor, Applicative, Monad
:Purpose: Lazy computation with side effects
:Operations: ``fmap``, ``pure``, ``ap``, ``bind``
:Operators: ``|`` (bind), ``**`` (ap)

.. code-block:: python

   from katharos.types import IO
   
   # Lazy computation
   io = IO(lambda: print("Hello"))
   # Nothing printed yet!
   
   io.run()  # Now it prints: Hello

Choosing the Right Type
-----------------------

Use this guide to select the appropriate type:

**For optional values:**
  - Use :class:`~katharos.types.Maybe`
  - Example: User lookup, configuration values

**For error handling:**
  - Use :class:`~katharos.types.Result`
  - Example: Parsing, validation, I/O operations

**For collections:**
  - Use :class:`~katharos.types.ImmutableList` for general lists
  - Use :class:`~katharos.types.NonEmptyList` when you need at least one element
  - Example: Processing sequences, aggregations

**For side effects:**
  - Use :class:`~katharos.types.IO`
  - Example: File I/O, network requests, printing

**For combining values:**
  - Use types with Monoid/Semigroup when you need to combine values
  - Example: Accumulating results, merging configurations

See Also
--------

- :doc:`../explanation/algebraic-abstractions` - Theory behind the hierarchy
- :doc:`../explanation/monad-laws` - Laws that govern these abstractions
- :doc:`operators` - Operator reference
