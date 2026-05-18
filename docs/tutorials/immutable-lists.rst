Working with Immutable Lists
====================================

Learn how to use ImmutableList and NonEmptyList for safe, functional collection operations.

What You'll Learn
-----------------

- How to create immutable lists that cannot be accidentally modified
- How to use NonEmptyList to guarantee at least one element at the type level
- How to use functional operations like ``map``, ``bind``, and ``concat``
- How immutability enables using lists as dictionary keys
- How covariance allows flexible type relationships

Creating Immutable Lists
------------------------

``ImmutableList`` wraps a standard Python list but prevents any modifications after creation:

.. code-block:: python

   from katharos.types import ImmutableList

   # Create from any iterable
   numbers = ImmutableList([1, 2, 3, 4, 5])
   words = ImmutableList(["hello", "world"])
   empty = ImmutableList([])

   # Standard sequence operations work
   print(len(numbers))        # 5
   print(3 in numbers)        # True
   print(numbers[0])          # 1
   print(list(numbers))       # [1, 2, 3, 4, 5]

   # Slicing is supported
   print(numbers[1:3])        # ImmutableList([2, 3])

Important: While the ``ImmutableList`` itself cannot be modified, the underlying data structure is not deeply immutable. If you store mutable objects, those objects can still be modified.

NonEmptyList: Lists That Always Have Elements
---------------------------------------------

``NonEmptyList`` guarantees at least one element at the type level. This is useful when you need to ensure operations like ``head()`` or ``reduce()`` are always safe:

.. code-block:: python

   from katharos.types import NonEmptyList

   # Must provide at least a head element
   nel = NonEmptyList(1, [2, 3, 4])  # head=1, tail=[2, 3, 4]

   # Access head and tail safely
   print(nel.head)  # 1
   print(nel.tail)  # [2, 3, 4]

   # Concatenation keeps the non-empty guarantee
   combined = nel + NonEmptyList(5, [6])
   print(combined)  # NonEmptyList([1, 2, 3, 4, 5, 6])

Concatenation
-------------

Both list types support concatenation with ``+`` or the ``@`` operator:

.. code-block:: python

   from katharos.types import ImmutableList, NonEmptyList

   # ImmutableList concatenation
   list1 = ImmutableList([1, 2])
   list2 = ImmutableList([3, 4])
   combined = list1 + list2
   print(combined)  # ImmutableList([1, 2, 3, 4])

   # Using @ operator (semigroup operation)
   also_combined = list1 @ list2
   print(also_combined)  # ImmutableList([1, 2, 3, 4])

   # NonEmptyList concatenation
   nel1 = NonEmptyList(1, [2])
   nel2 = NonEmptyList(3, [4])
   nel_combined = nel1 + nel2
   print(nel_combined)  # NonEmptyList([1, 2, 3, 4])

   # Note: Empty list + NonEmptyList is allowed
   empty = ImmutableList([])
   result = empty + NonEmptyList(1, [2])
   print(result)  # NonEmptyList([1, 2])

Hashability: Using Lists as Dictionary Keys
------------------------------------------

Because ``ImmutableList`` and ``NonEmptyList`` are truly immutable, they can be used as dictionary keys or stored in sets:

.. code-block:: python

   from katharos.types import ImmutableList

   # Create a cache with list keys
   cache: dict[ImmutableList[int], str] = {
       ImmutableList([1, 2, 3]): "triangle",
       ImmutableList([4, 5, 6]): "other triangle",
   }

   # Works with sets too
   unique_lists = {
       ImmutableList([1, 2]),
       ImmutableList([1, 2]),  # Duplicate, won't be added
       ImmutableList([3, 4]),
   }
   print(len(unique_lists))  # 2

Functor: Transforming Elements
------------------------------

Use ``fmap`` to apply a function to every element, returning a new list:

.. code-block:: python

   from katharos.types import ImmutableList, NonEmptyList

   numbers = ImmutableList([1, 2, 3, 4, 5])

   # Double every number
   doubled = numbers.fmap(lambda x: x * 2)
   print(doubled)  # ImmutableList([2, 4, 6, 8, 10])

   # Convert to strings
   strings = numbers.fmap(str)
   print(strings)  # ImmutableList(['1', '2', '3', '4', '5'])

   # Works with NonEmptyList too
   nel = NonEmptyList(1, [2, 3])
   tripled = nel.fmap(lambda x: x * 3)
   print(tripled)  # NonEmptyList([3, 6, 9])

Applicative: Applying Wrapped Functions
-----------------------------------------

The applicative interface lets you apply functions that are themselves wrapped in the list:

.. code-block:: python

   from katharos.types import ImmutableList

   numbers = ImmutableList([1, 2, 3])

   # List of functions
   funcs = ImmutableList([
       lambda x: x + 1,
       lambda x: x * 2,
   ])

   # Apply each function to each number (cartesian product)
   result = numbers.ap(funcs)
   print(result)  # ImmutableList([2, 3, 4, 2, 4, 6])

   # Using the ** operator for applicative style
   result_alt = numbers ** funcs
   print(result_alt)  # Same as above

Monad: Chaining Operations with FlatMap
---------------------------------------

Use ``bind`` (or the ``|`` operator) to chain operations where each step returns a new list:

.. code-block:: python

   from katharos.types import ImmutableList

   numbers = ImmutableList([1, 2, 3])

   # For each number, return a list of [n, n*2]
   def duplicate_and_double(n: int) -> ImmutableList[int]:
       return ImmutableList([n, n * 2])

   # Chain the operation
   result = numbers.bind(duplicate_and_double)
   print(result)  # ImmutableList([1, 2, 2, 4, 3, 6])

   # Using | operator
   result_alt = numbers | duplicate_and_double
   print(result_alt)  # Same as above

   # NonEmptyList version
   from katharos.types import NonEmptyList

   nel = NonEmptyList(1, [2])
   nel_result = nel | (lambda n: NonEmptyList(n, [n * 2]))
   print(nel_result)  # NonEmptyList([1, 2, 2, 4])

Monoid: Combining Lists
-----------------------

``ImmutableList`` is a monoid with an identity element (empty list) and an associative operation (concatenation):

.. code-block:: python

   from katharos.types import ImmutableList

   # Identity element is an empty list
   empty = ImmutableList.identity()
   print(empty)  # ImmutableList([])

   # Monoid operation (same as + or @)
   list1 = ImmutableList([1, 2])
   list2 = ImmutableList([3, 4])
   combined = list1.op(list2)
   print(combined)  # ImmutableList([1, 2, 3, 4])

   # Monoid laws hold:
   # 1. Identity: empty + list = list
   # 2. Associativity: (a + b) + c = a + (b + c)

Type Covariance
---------------

Both list types are covariant, meaning ``ImmutableList[Child]`` is a subtype of ``ImmutableList[Parent]`` when ``Child`` is a subtype of ``Parent``:

.. code-block:: python

   from katharos.types import ImmutableList, NonEmptyList

   class Animal:
       def speak(self) -> str:
           return "..."

   class Dog(Animal):
       def speak(self) -> str:
           return "Woof!"

   # Covariance allows this assignment
   dogs: ImmutableList[Dog] = ImmutableList([Dog(), Dog()])
   animals: ImmutableList[Animal] = dogs  # Valid!

   # Works with NonEmptyList too
   more_dogs = NonEmptyList(Dog(), [Dog()])
   more_animals: NonEmptyList[Animal] = more_dogs  # Valid!

Practical Example: Safe List Processing
---------------------------------------

Here's a practical example combining multiple features:

.. code-block:: python

   from katharos.types import ImmutableList, NonEmptyList
   from dataclasses import dataclass

   @dataclass(frozen=True)
   class Product:
       name: str
       price: float
       category: str

   # Create an immutable product list
   products = ImmutableList([
       Product("Laptop", 999.99, "electronics"),
       Product("Book", 19.99, "books"),
       Product("Phone", 699.99, "electronics"),
   ])

   # Safe operations that can't modify original
   electronics = products.fmap(
       lambda p: p if p.category == "electronics" else None
   )

   # Calculate total using bind and monoid
   prices = products.fmap(lambda p: p.price)

   # Create a NonEmptyList for safe reduction
   if len(prices) > 0:
       price_nel = NonEmptyList(prices[0], list(prices[1:]))
       total = price_nel.head + sum(price_nel.tail)
       print(f"First price: {price_nel.head}, Total: {total}")

   # Use as dictionary key for caching
   cache_key = products  # ImmutableList is hashable!
   cached_result = {cache_key: "processed"}

Comparison: ImmutableList vs NonEmptyList
------------------------------------------

+------------------+--------------------------------+--------------------------------+
| Feature          | ImmutableList                  | NonEmptyList                   |
+==================+================================+================================+
| Empty allowed    | ✅ Yes                         | ❌ No (at least 1 element)     |
+------------------+--------------------------------+--------------------------------+
| Monoid           | ✅ Yes (identity element)      | ❌ No (only Semigroup)         |
+------------------+--------------------------------+--------------------------------+
| Safe head/tail   | ❌ May raise IndexError        | ✅ Always safe                 |
+------------------+--------------------------------+--------------------------------+
| Concatenation    | Preserves type                 | Preserves NonEmptyList         |
+------------------+--------------------------------+--------------------------------+
| Functor/Applicative| ✅ Yes                       | ✅ Yes                         |
+------------------+--------------------------------+--------------------------------+
| Monad            | ✅ Yes                         | ✅ Yes                         |
+------------------+--------------------------------+--------------------------------+

What You've Learned
-------------------

Congratulations! You now understand:

- ✅ How to create and use ``ImmutableList`` for guaranteed immutability
- ✅ How ``NonEmptyList`` provides compile-time guarantees of non-emptiness
- ✅ How to concatenate lists with ``+`` and ``@`` operators
- ✅ How immutability enables hashability for dictionary keys
- ✅ How to use ``fmap`` for transforming elements
- ✅ How to use ``bind`` (``|``) for chaining list operations
- ✅ How applicative functors apply wrapped functions
- ✅ How type covariance provides flexible type relationships

Next Steps
----------

- Learn about :doc:`do-syntax` to simplify monadic chains
- Explore :doc:`error-handling` with ``Maybe`` and ``Result`` types
- Read :doc:`../explanation/algebraic-abstractions` for theory

Further Reading
---------------

- :class:`katharos.types.ImmutableList` - API reference
- :class:`katharos.types.NonEmptyList` - API reference
- :doc:`../reference/type-hierarchy` - Type hierarchy
