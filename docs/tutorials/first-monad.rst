Your First Monadic Computation
===============================

In this tutorial, you'll learn about monads and how to use the bind operation (``|`` operator) to chain computations that return wrapped values.

What You'll Learn
-----------------

- What monads are and why they're useful
- How to use the bind operation (``|``)
- The difference between ``fmap`` and ``bind``
- How to chain operations that return ``Maybe``

Prerequisites
-------------

Complete the :doc:`getting-started` tutorial first to understand ``Maybe`` basics.

Understanding the Problem
-------------------------

In the previous tutorial, we used ``fmap`` to apply functions to values inside ``Maybe``. But what if our function *also* returns a ``Maybe``?

.. code-block:: python

   from katharos.types import Maybe

   def safe_sqrt(x: float) -> Maybe[float]:
       """Return the square root, or Nothing if x is negative."""
       if x < 0:
           return Maybe.Nothing()
       return Maybe.Just(x ** 0.5)

   # This doesn't work well with fmap!
   result = Maybe.Just(16).fmap(safe_sqrt)
   print(result)  # Just(Just(4.0)) - nested Maybe!

We get a nested ``Maybe[Maybe[float]]`` instead of ``Maybe[float]``. This is where monads come in!

Introducing Bind
----------------

The bind operation (``|`` operator) solves this problem. It applies a function that returns a wrapped value and automatically flattens the result:

.. code-block:: python

   from katharos.types import Maybe

   def safe_sqrt(x: float) -> Maybe[float]:
       if x < 0:
           return Maybe.Nothing()
       return Maybe.Just(x ** 0.5)

   # Using bind (|) instead of fmap
   result = Maybe.Just(16) | safe_sqrt
   print(result)  # Just(4.0) - no nesting!

   # With a negative number
   result = Maybe.Just(-4) | safe_sqrt
   print(result)  # Nothing()

   # With Nothing
   result = Maybe.Nothing() | safe_sqrt
   print(result)  # Nothing()

Chaining Monadic Operations
----------------------------

The real power of bind is in chaining multiple operations:

.. code-block:: python

   from katharos.types import Maybe

   def safe_divide(a: float, b: float) -> Maybe[float]:
       if b == 0:
           return Maybe.Nothing()
       return Maybe.Just(a / b)

   def safe_sqrt(x: float) -> Maybe[float]:
       if x < 0:
           return Maybe.Nothing()
       return Maybe.Just(x ** 0.5)

   def safe_log(x: float) -> Maybe[float]:
       if x <= 0:
           return Maybe.Nothing()
       import math
       return Maybe.Just(math.log(x))

   # Chain operations: divide, then sqrt, then log
   result = (
       Maybe.Just(100)
       | (lambda x: safe_divide(x, 4))  # 100 / 4 = 25
       | safe_sqrt                       # sqrt(25) = 5
       | safe_log                        # log(5) ≈ 1.609
   )
   print(result)  # Just(1.6094379124341003)

   # If any step fails, the whole chain short-circuits
   result = (
       Maybe.Just(100)
       | (lambda x: safe_divide(x, 0))  # Division by zero!
       | safe_sqrt                       # Never executed
       | safe_log                        # Never executed
   )
   print(result)  # Nothing()

When to Use fmap vs bind
-------------------------

Use ``fmap`` when:
  Your function returns a plain value (not wrapped in ``Maybe``)

.. code-block:: python

   Maybe.Just(5).fmap(lambda x: x * 2)  # Just(10)

Use ``bind`` (``|``) when:
  Your function returns a ``Maybe`` (or another monad)

.. code-block:: python

   Maybe.Just(16) | safe_sqrt  # Just(4.0)

Practical Example: User Lookup
-------------------------------

Let's build a realistic example with user data:

.. code-block:: python

   from katharos.types import Maybe

   # Simulated database
   users = {
       1: {"name": "Alice", "manager_id": 2},
       2: {"name": "Bob", "manager_id": 3},
       3: {"name": "Charlie", "manager_id": None},
   }

   def get_user(user_id: int) -> Maybe[dict]:
       """Look up a user by ID."""
       user = users.get(user_id)
       if user is None:
           return Maybe.Nothing()
       return Maybe.Just(user)

   def get_manager_id(user: dict) -> Maybe[int]:
       """Get the manager ID from a user."""
       manager_id = user.get("manager_id")
       if manager_id is None:
           return Maybe.Nothing()
       return Maybe.Just(manager_id)

   # Find Alice's manager's manager
   result = (
       get_user(1)                    # Get Alice
       | get_manager_id               # Get her manager's ID (2)
       | get_user                     # Get Bob
       | get_manager_id               # Get his manager's ID (3)
       | get_user                     # Get Charlie
   )

   if result.is_just():
       print(f"Found: {result.unwrap()['name']}")  # Found: Charlie
   else:
       print("Not found")

   # Try with a user who doesn't exist
   result = get_user(999) | get_manager_id | get_user
   print(result)  # Nothing()

Using ret (pure)
----------------

Sometimes you need to wrap a plain value in a monad. Use ``ret`` (or ``pure``):

.. code-block:: python

   from katharos.types import Maybe

   # Wrap a value
   wrapped = Maybe.ret(42)
   print(wrapped)  # Just(42)

   # Useful in chains
   result = (
       Maybe.Just(5)
       | (lambda x: Maybe.ret(x * 2) if x > 0 else Maybe.Nothing())
   )
   print(result)  # Just(10)

The Monad Laws
--------------

Monads follow three laws that ensure predictable behavior:

1. **Left Identity**: ``Maybe.ret(x) | f`` equals ``f(x)``

.. code-block:: python

   def f(x): return Maybe.Just(x * 2)
   
   # These are equivalent
   result1 = Maybe.ret(5) | f
   result2 = f(5)
   print(result1 == result2)  # True

2. **Right Identity**: ``m | Maybe.ret`` equals ``m``

.. code-block:: python

   m = Maybe.Just(5)
   result = m | Maybe.ret
   print(result == m)  # True

3. **Associativity**: ``(m | f) | g`` equals ``m | (lambda x: f(x) | g)``

.. code-block:: python

   m = Maybe.Just(5)
   f = lambda x: Maybe.Just(x * 2)
   g = lambda x: Maybe.Just(x + 3)
   
   result1 = (m | f) | g
   result2 = m | (lambda x: f(x) | g)
   print(result1 == result2)  # True

What You've Learned
-------------------

Congratulations! You now understand:

- ✅ What monads are and why they're useful
- ✅ How to use bind (``|``) to chain monadic operations
- ✅ The difference between ``fmap`` and ``bind``
- ✅ How to use ``ret``/``pure`` to wrap values
- ✅ The three monad laws

Next Steps
----------

- Learn about :doc:`do-syntax` for cleaner, more readable monadic code
- Explore :doc:`error-handling` with the ``Result`` monad
- Read :doc:`../explanation/monad-laws` for deeper understanding

Further Reading
---------------

- :class:`katharos.algebra.Monad` - API reference
- :doc:`../explanation/algebraic-abstractions` - Theory behind monads
- :doc:`../how-to/chain-operations` - Advanced patterns
