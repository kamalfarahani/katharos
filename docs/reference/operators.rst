Operator Reference
==================

Katharos provides several operators for convenient functional composition. This reference documents all available operators and their usage.

Functor Operators
-----------------

fmap (method)
~~~~~~~~~~~~~

Maps a function over a functor.

**Syntax:** ``functor.fmap(f)``

**Example:**

.. code-block:: python

   from katharos.types import Maybe
   
   result = Maybe.Just(5).fmap(lambda x: x * 2)
   # Just(10)

Applicative Operators
---------------------

\*\* (power)
~~~~~~~~~~~~

Applies a wrapped function to a wrapped value.

**Syntax:** ``value ** wrapped_function``

**Example:**

.. code-block:: python

   from katharos.types import Maybe
   
   add = lambda x: lambda y: x + y
   result = Maybe.Just(3) ** Maybe.Just(add(5))
   # Just(8)

Monad Operators
---------------

| (pipe/bind)
~~~~~~~~~~~~~

Binds a monadic computation, sequencing operations that return wrapped values.

**Syntax:** ``monad | function``

**Example:**

.. code-block:: python

   from katharos.types import Maybe
   
   def safe_sqrt(x):
       if x < 0:
           return Maybe.Nothing()
       return Maybe.Just(x ** 0.5)
   
   result = Maybe.Just(16) | safe_sqrt
   # Just(4.0)

>> (then)
~~~~~~~~~

Sequences two monadic actions, discarding the result of the first.

**Syntax:** ``monad1 >> monad2``

**Example:**

.. code-block:: python

   from katharos.types import Maybe
   
   result = Maybe.Just(5) >> Maybe.Just(10)
   # Just(10)

Semigroup Operators
-------------------

@ (matmul)
~~~~~~~~~~

Combines two semigroup values using the semigroup operation.

**Syntax:** ``semigroup1 @ semigroup2``

**Example:**

.. code-block:: python

   from katharos.types import NonEmptyList
   
   list1 = NonEmptyList(1, [2, 3])
   list2 = NonEmptyList(4, [5, 6])
   result = list1 @ list2
   # NonEmptyList(1, [2, 3, 4, 5, 6])

Operator Precedence
-------------------

When combining operators, Python's operator precedence applies:

1. ``**`` (highest precedence)
2. ``@``
3. ``>>``
4. ``|`` (lowest precedence)

**Example:**

.. code-block:: python

   # These are equivalent:
   result1 = (m | f) | g
   result2 = m | f | g  # Left-associative

Use parentheses for clarity when combining different operators.

Operator Chaining
-----------------

Most operators can be chained for fluent composition:

.. code-block:: python

   from katharos.types import Maybe
   
   result = (
       Maybe.Just(5)
       .fmap(lambda x: x * 2)      # Just(10)
       .fmap(lambda x: x + 3)      # Just(13)
       | (lambda x: Maybe.Just(x ** 2))  # Just(169)
   )

Type-Specific Operators
-----------------------

Some types provide additional operators. See their respective API documentation:

- :class:`katharos.types.Maybe` - ``|``, ``**``
- :class:`katharos.types.Result` - ``|``, ``**``
- :class:`katharos.types.ImmutableList` - ``+``, ``|``, ``**``, ``@``
- :class:`katharos.types.NonEmptyList` - ``@``, ``|``, ``**``
- :class:`katharos.types.IO` - ``|``
