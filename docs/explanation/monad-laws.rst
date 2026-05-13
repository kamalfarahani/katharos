Monad Laws and Their Importance
================================

Monads must satisfy three fundamental laws. Understanding these laws helps you write correct, predictable code and reason about monadic computations.

Why Laws Matter
---------------

Mathematical laws aren't just theoretical - they provide guarantees about how your code behaves:

**Predictability**
  Laws ensure consistent behavior across different monads

**Composability**
  Laws guarantee that operations can be safely combined

**Refactoring**
  Laws allow you to restructure code without changing its meaning

**Optimization**
  Compilers and interpreters can optimize based on laws

The Three Monad Laws
---------------------

Every monad must satisfy three laws. We'll explore each using the ``Maybe`` monad.

Law 1: Left Identity
~~~~~~~~~~~~~~~~~~~~~

**Statement:** ``pure(x) | f`` equals ``f(x)``

Wrapping a value and immediately binding it should be the same as just calling the function.

.. code-block:: python

   from katharos.types import Maybe
   
   def f(x: int) -> Maybe[int]:
       return Maybe.Just(x * 2)
   
   x = 5
   
   # These should be equal
   result1 = Maybe.pure(x) | f
   result2 = f(x)
   
   print(result1)  # Just(10)
   print(result2)  # Just(10)
   print(result1 == result2)  # True

**Why it matters:**

This law says that ``pure`` (or ``ret``) is a neutral wrapper - it doesn't add any behavior. This is crucial for composition because you can introduce or remove ``pure`` without changing the program's meaning.

**Real-world analogy:**

Putting something in a transparent box and immediately taking it out is the same as never boxing it at all.

Law 2: Right Identity
~~~~~~~~~~~~~~~~~~~~~~

**Statement:** ``m | pure`` equals ``m``

Binding a monad with ``pure`` should return the original monad unchanged.

.. code-block:: python

   from katharos.types import Maybe
   
   m = Maybe.Just(5)
   
   # These should be equal
   result1 = m | Maybe.pure
   result2 = m
   
   print(result1)  # Just(5)
   print(result2)  # Just(5)
   print(result1 == result2)  # True
   
   # Also works with Nothing
   n = Maybe.Nothing()
   print(n | Maybe.pure == n)  # True

**Why it matters:**

This law ensures that ``pure`` is truly neutral - it doesn't transform or wrap the value further. You can always add ``| pure`` at the end of a chain without changing behavior.

**Real-world analogy:**

Taking something out of a box and putting it back in the same type of box gives you the same thing.

Law 3: Associativity
~~~~~~~~~~~~~~~~~~~~

**Statement:** ``(m | f) | g`` equals ``m | (lambda x: f(x) | g)``

The order of binding operations doesn't matter - you can group them however you want.

.. code-block:: python

   from katharos.types import Maybe
   
   def f(x: int) -> Maybe[int]:
       return Maybe.Just(x * 2)
   
   def g(x: int) -> Maybe[int]:
       return Maybe.Just(x + 3)
   
   m = Maybe.Just(5)
   
   # These should be equal
   result1 = (m | f) | g
   result2 = m | (lambda x: f(x) | g)
   
   print(result1)  # Just(13)
   print(result2)  # Just(13)
   print(result1 == result2)  # True

**Why it matters:**

This is the most important law for composition. It means you can refactor chains of operations without worrying about breaking your code. You can extract parts of a chain into separate functions.

**Real-world analogy:**

When following a series of directions, it doesn't matter if you think of them as (A then B) then C, or A then (B then C) - you end up in the same place.

Practical Implications
----------------------

Refactoring with Confidence
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The laws allow safe refactoring:

.. code-block:: python

   from katharos.types import Maybe
   
   def safe_sqrt(x: float) -> Maybe[float]:
       if x < 0:
           return Maybe.Nothing()
       return Maybe.Just(x ** 0.5)
   
   def safe_log(x: float) -> Maybe[float]:
       if x <= 0:
           return Maybe.Nothing()
       import math
       return Maybe.Just(math.log(x))
   
   # Original code
   result = Maybe.Just(16) | safe_sqrt | safe_log
   
   # Can extract into a helper function (associativity)
   def sqrt_then_log(x: float) -> Maybe[float]:
       return safe_sqrt(x) | safe_log
   
   result = Maybe.Just(16) | sqrt_then_log
   
   # Both produce the same result!

Eliminating Redundant Wrapping
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Left identity lets you simplify code:

.. code-block:: python

   from katharos.types import Maybe
   
   def process(x: int) -> Maybe[int]:
       return Maybe.Just(x * 2)
   
   # Redundant
   result = Maybe.pure(5) | process
   
   # Simplified (by left identity)
   result = process(5)

Composing Functions
~~~~~~~~~~~~~~~~~~~

Associativity enables function composition:

.. code-block:: python

   from katharos.types import Maybe
   
   def f(x: int) -> Maybe[int]:
       return Maybe.Just(x * 2)
   
   def g(x: int) -> Maybe[int]:
       return Maybe.Just(x + 3)
   
   # Compose f and g into a single function
   def f_then_g(x: int) -> Maybe[int]:
       return f(x) | g
   
   # Use it
   result = Maybe.Just(5) | f_then_g
   # Same as: (Maybe.Just(5) | f) | g

Verifying the Laws
------------------

Let's verify all three laws for ``Maybe``:

.. code-block:: python

   from katharos.types import Maybe
   
   def f(x: int) -> Maybe[int]:
       return Maybe.Just(x * 2)
   
   def g(x: int) -> Maybe[int]:
       return Maybe.Just(x + 3)
   
   # Test with Just
   print("Testing with Just(5):")
   
   # Left identity
   assert Maybe.pure(5) | f == f(5)
   print("✓ Left identity")
   
   # Right identity
   m = Maybe.Just(5)
   assert m | Maybe.pure == m
   print("✓ Right identity")
   
   # Associativity
   assert (m | f) | g == m | (lambda x: f(x) | g)
   print("✓ Associativity")
   
   # Test with Nothing
   print("\nTesting with Nothing:")
   n = Maybe.Nothing()
   
   # Right identity
   assert n | Maybe.pure == n
   print("✓ Right identity")
   
   # Associativity
   assert (n | f) | g == n | (lambda x: f(x) | g)
   print("✓ Associativity")

Laws for Other Monads
---------------------

All monads in Katharos satisfy these laws:

Result
~~~~~~

.. code-block:: python

   from katharos.types import Result
   
   def f(x: int) -> Result[Exception, int]:
       return Result.Success(x * 2)
   
   # Left identity
   assert Result.pure(5) | f == f(5)
   
   # Right identity
   m = Result.Success(5)
   assert m | Result.pure == m
   
   # Associativity
   def g(x): return Result.Success(x + 3)
   assert (m | f) | g == m | (lambda x: f(x) | g)

ImmutableList
~~~~~~~~~~~~~

.. code-block:: python

   from katharos.types import ImmutableList
   
   def f(x: int) -> ImmutableList[int]:
       return ImmutableList([x, x * 2])
   
   # Left identity
   assert ImmutableList.pure(5) | f == f(5)
   
   # Right identity
   m = ImmutableList([1, 2, 3])
   assert m | ImmutableList.pure == m
   
   # Associativity
   def g(x): return ImmutableList([x, x + 1])
   assert (m | f) | g == m | (lambda x: f(x) | g)

When Laws Are Broken
--------------------

What happens if a type claims to be a monad but doesn't follow the laws?

**Unpredictable behavior:**

.. code-block:: python

   # Hypothetical broken monad
   class BrokenMaybe:
       def __or__(self, f):
           # Adds extra behavior - breaks left identity!
           result = f(self.value)
           print("Side effect!")  # Shouldn't be here
           return result

   # Now refactoring changes behavior
   result1 = BrokenMaybe.pure(5) | f  # Prints "Side effect!"
   result2 = f(5)                      # Doesn't print anything
   # result1 != result2 - left identity broken!

**Broken composition:**

If associativity is broken, you can't safely refactor chains of operations.

Common Pitfalls
---------------

Side Effects in Bind
~~~~~~~~~~~~~~~~~~~~

Don't add side effects in the bind operation:

.. code-block:: python

   # BAD - breaks laws
   class BadMonad:
       def __or__(self, f):
           print("Binding!")  # Side effect!
           return f(self.value)
   
   # GOOD - side effects in IO monad
   from katharos.types import IO
   
   io = IO(lambda: print("Hello"))  # Side effect contained
   result = io | (lambda _: IO(lambda: print("World")))

Stateful Operations
~~~~~~~~~~~~~~~~~~~

Don't use mutable state in monadic operations:

.. code-block:: python

   # BAD - breaks laws
   counter = 0
   def bad_f(x):
       global counter
       counter += 1  # Mutable state!
       return Maybe.Just(x + counter)
   
   # Now left identity is broken:
   # Maybe.pure(5) | bad_f != bad_f(5)

Testing Your Own Monads
-----------------------

If you implement a custom monad, test the laws:

.. code-block:: python

   def test_monad_laws(monad_class, pure_value, f, g):
       """Test that a monad satisfies the three laws."""
       m = monad_class.pure(pure_value)
       
       # Left identity
       assert monad_class.pure(pure_value) | f == f(pure_value)
       
       # Right identity
       assert m | monad_class.pure == m
       
       # Associativity
       assert (m | f) | g == m | (lambda x: f(x) | g)
       
       print("All monad laws satisfied! ✓")

Further Reading
---------------

- :doc:`algebraic-abstractions` - The theory behind monads
- :doc:`fp-concepts` - Core functional programming concepts
- :doc:`../tutorials/first-monad` - Practical monad usage
- :doc:`../reference/type-hierarchy` - Which types are monads

Mathematical Background
-----------------------

The monad laws come from category theory:

- **Left identity** corresponds to the left unit law
- **Right identity** corresponds to the right unit law
- **Associativity** corresponds to the associativity of composition

In category theory notation:

.. code-block:: text

   Left identity:    η(x) >>= f  =  f(x)
   Right identity:   m >>= η      =  m
   Associativity:    (m >>= f) >>= g  =  m >>= (λx. f(x) >>= g)

Where:
- ``η`` (eta) is ``pure``/``ret``
- ``>>=`` is bind (``|`` in Katharos)
- ``λx`` is a lambda function

You don't need to understand category theory to use monads, but it provides a rigorous mathematical foundation for these laws.
