Understanding Functional Programming Concepts
============================================

This article explains the core concepts of functional programming and how they're implemented in Katharos.

What is Functional Programming?
--------------------------------

Functional programming (FP) is a programming paradigm that treats computation as the evaluation of mathematical functions. It emphasizes:

- **Immutability**: Data cannot be modified after creation
- **Pure functions**: Functions always produce the same output for the same input
- **Composition**: Building complex operations from simple ones
- **Higher-order functions**: Functions that take or return other functions

Why Functional Programming?
----------------------------

Functional programming offers several benefits:

**Predictability**
  Pure functions are easier to reason about because they don't depend on or modify external state.

**Testability**
  Pure functions are trivial to test - just check inputs and outputs.

**Composability**
  Small, focused functions can be combined to create complex behaviors.

**Concurrency**
  Immutable data eliminates race conditions and makes concurrent programming safer.

**Maintainability**
  Code is more modular and changes have limited scope.

Core Concepts in Katharos
--------------------------

Immutability
~~~~~~~~~~~~

All data structures in Katharos are immutable. Once created, they cannot be changed:

.. code-block:: python

   from katharos.types import ImmutableList
   
   list1 = ImmutableList([1, 2, 3])
   list2 = list1 + [4, 5]  # Creates a new list
   
   print(list1)  # ImmutableList([1, 2, 3]) - unchanged!
   print(list2)  # ImmutableList([1, 2, 3, 4, 5])

**Benefits:**
- No unexpected mutations
- Safe to share data across functions
- Easier to reason about program state

Pure Functions
~~~~~~~~~~~~~~

A pure function:
1. Always returns the same output for the same input
2. Has no side effects (doesn't modify external state)

.. code-block:: python

   # Pure function
   def add(x: int, y: int) -> int:
       return x + y
   
   # Impure function (has side effects)
   counter = 0
   def increment():
       global counter
       counter += 1  # Modifies external state!
       return counter

**In Katharos:**
Most operations are pure. Side effects are isolated in the ``IO`` type.

Function Composition
~~~~~~~~~~~~~~~~~~~~

Composition means combining simple functions to create more complex ones:

.. code-block:: python

   from katharos.functools import F
   
   # Simple functions
   def double(x: int) -> int:
       return x * 2
   
   def add_three(x: int) -> int:
       return x + 3
   
   # Compose them
   double_then_add = F.compose(add_three)(double)
   
   result = double_then_add(5)  # (5 * 2) + 3 = 13

**Mathematical notation:** ``(f ∘ g)(x) = f(g(x))``

Higher-Order Functions
~~~~~~~~~~~~~~~~~~~~~~

Functions that take functions as arguments or return functions:

.. code-block:: python

   from katharos.types import ImmutableList
   
   # fmap is a higher-order function
   numbers = ImmutableList([1, 2, 3, 4, 5])
   doubled = numbers.fmap(lambda x: x * 2)
   # ImmutableList([2, 4, 6, 8, 10])

**Common patterns:**
- ``map``: Apply a function to each element
- ``filter``: Select elements matching a predicate
- ``fold``: Reduce a collection to a single value

Algebraic Data Types
~~~~~~~~~~~~~~~~~~~~

Types defined by their structure and operations, following mathematical laws:

.. code-block:: python

   from katharos.types import Maybe
   
   # Maybe is an algebraic data type with two constructors:
   just_value = Maybe.Just(42)    # Contains a value
   nothing = Maybe.Nothing()       # Contains no value

**Key insight:** The type's behavior is defined by its algebra, not by implementation details.

Referential Transparency
~~~~~~~~~~~~~~~~~~~~~~~~

An expression is referentially transparent if it can be replaced with its value without changing the program's behavior:

.. code-block:: python

   # Referentially transparent
   x = 2 + 3
   y = x * 2
   # Can replace x with 5:
   y = 5 * 2  # Same result!
   
   # Not referentially transparent
   x = random.randint(1, 10)
   y = x * 2
   # Can't replace x with its value - it changes each time!

**In Katharos:** Pure functions and immutable data ensure referential transparency.

Type Safety
~~~~~~~~~~~

Katharos uses Python's type system to catch errors at development time:

.. code-block:: python

   from katharos.types import Maybe
   
   def safe_divide(a: float, b: float) -> Maybe[float]:
       if b == 0:
           return Maybe.Nothing()
       return Maybe.Just(a / b)
   
   # Type checker knows the return type is Maybe[float]
   result: Maybe[float] = safe_divide(10, 2)

**Benefits:**
- Catch errors before runtime
- Self-documenting code
- Better IDE support

Laziness
~~~~~~~~

Lazy evaluation delays computation until the result is needed:

.. code-block:: python

   from katharos.types import IO
   
   # This doesn't print immediately
   io = IO(lambda: print("Hello, World!"))
   
   # Computation happens only when we run it
   io.run()  # Now it prints

**Benefits:**
- Efficient resource usage
- Ability to work with infinite structures
- Separation of definition from execution

Practical Application
---------------------

Let's see how these concepts work together in a real example:

.. code-block:: python

   from katharos.types import Maybe, ImmutableList
   from katharos.functools import F
   
   # Pure functions
   def parse_int(s: str) -> Maybe[int]:
       try:
           return Maybe.Just(int(s))
       except ValueError:
           return Maybe.Nothing()
   
   def is_positive(x: int) -> bool:
       return x > 0
   
   def square(x: int) -> int:
       return x * x
   
   # Immutable data
   inputs = ImmutableList(["1", "2", "invalid", "3", "-4", "5"])
   
   # Composition and higher-order functions
   results = (
       inputs
       .fmap(parse_int)                    # ImmutableList[Maybe[int]]
       .fmap(lambda m: m.fmap(square))     # Square each valid number
   )
   
   # Extract valid results
   valid_results = [
       m.unwrap() for m in results 
       if m.is_just() and is_positive(m.unwrap())
   ]
   
   print(valid_results)  # [1, 4, 9, 25]

This example demonstrates:
- ✅ Immutability (ImmutableList)
- ✅ Pure functions (parse_int, square)
- ✅ Composition (chaining operations)
- ✅ Higher-order functions (fmap)
- ✅ Type safety (Maybe for error handling)

Comparison with Imperative Style
---------------------------------

**Imperative approach:**

.. code-block:: python

   inputs = ["1", "2", "invalid", "3", "-4", "5"]
   results = []
   
   for s in inputs:
       try:
           n = int(s)
           if n > 0:
               results.append(n * n)
       except ValueError:
           pass  # Skip invalid inputs

**Functional approach:**

.. code-block:: python

   from katharos.types import ImmutableList
   
   results = (
       ImmutableList(["1", "2", "invalid", "3", "-4", "5"])
       .fmap(parse_int)
       .fmap(lambda m: m.fmap(lambda x: x * x if x > 0 else None))
   )

The functional approach:
- Makes data flow explicit
- Separates concerns (parsing, filtering, transformation)
- Is more composable and reusable
- Eliminates mutable state

Common Misconceptions
---------------------

"Functional programming is slower"
  Modern FP implementations are highly optimized. The benefits in correctness and maintainability often outweigh minor performance differences.

"You can't do I/O in functional programming"
  FP isolates side effects (like I/O) in special types (like ``IO``), making them explicit and controlled.

"Functional programming is only for academics"
  FP concepts are used in production systems at companies like Facebook, Twitter, and Microsoft.

"You need to learn category theory"
  While category theory inspires FP, you don't need to understand it to use Katharos effectively.

Next Steps
----------

- Learn about :doc:`algebraic-abstractions` to understand the theory
- Explore :doc:`monad-laws` to see how laws ensure correctness
- Read :doc:`immutability` for deep dive into immutable data structures
- Check out :doc:`comparison` to see how Katharos compares to other libraries

Further Reading
---------------

- `Functional Programming in Python <https://docs.python.org/3/howto/functional.html>`_ (Python docs)
- `Why Functional Programming Matters <https://www.cs.kent.ac.uk/people/staff/dat/miranda/whyfp90.pdf>`_ (John Hughes)
- :doc:`../tutorials/getting-started` - Start coding with Katharos
