Getting Started with Katharos
==============================

Welcome to Katharos! This tutorial will guide you through installing Katharos and writing your first functional program.

What You'll Build
-----------------

By the end of this tutorial, you'll have:

- Installed Katharos in your Python environment
- Written a simple program using Maybe for safe optional values
- Understood the basics of functional composition

Prerequisites
-------------

- Python 3.13 or later
- Basic understanding of Python functions and type hints
- pip package manager

Step 1: Installation
---------------------

Install Katharos using pip:

.. code-block:: bash

   pip install katharos

Verify the installation by importing Katharos in a Python shell:

.. code-block:: python

   >>> import katharos
   >>> from katharos.types import Maybe
   >>> print("Katharos installed successfully!")
   Katharos installed successfully!

Step 2: Your First Maybe
-------------------------

The ``Maybe`` type represents an optional value. It's a type-safe alternative to using ``None``.

Create a new Python file called ``hello_katharos.py``:

.. code-block:: python

   from katharos.types import Maybe

   # Create a Maybe with a value
   just_value = Maybe.Just(42)
   print(just_value)  # Just(42)

   # Create an empty Maybe
   nothing_value = Maybe.Nothing()
   print(nothing_value)  # Nothing()

Run the file:

.. code-block:: bash

   python hello_katharos.py

You should see:

.. code-block:: text

   Just(42)
   Nothing()

Step 3: Mapping Over Maybe
---------------------------

One of the most powerful features of ``Maybe`` is the ability to map functions over it safely:

.. code-block:: python

   from katharos.types import Maybe

   def double(x: int) -> int:
       return x * 2

   # Map over a Just value
   result = Maybe.Just(5).fmap(double)
   print(result)  # Just(10)

   # Map over Nothing - the function is never called!
   result = Maybe.Nothing().fmap(double)
   print(result)  # Nothing()

The key insight: when you map over ``Nothing``, the function is never executed. This prevents errors and makes your code safer.

Step 4: Chaining Operations
----------------------------

You can chain multiple operations together:

.. code-block:: python

   from katharos.types import Maybe

   result = (
       Maybe.Just(5)
       .fmap(lambda x: x * 2)      # Just(10)
       .fmap(lambda x: x + 3)      # Just(13)
       .fmap(lambda x: x ** 2)     # Just(169)
   )
   print(result)  # Just(169)

Step 5: Extracting Values
--------------------------

To get the value out of a ``Maybe``, use the ``unwrap()`` method:

.. code-block:: python

   from katharos.types import Maybe

   just_value = Maybe.Just(42)
   value = just_value.unwrap()
   print(value)  # 42

   # Be careful! Unwrapping Nothing raises an error
   try:
       nothing_value = Maybe.Nothing()
       value = nothing_value.unwrap()
   except ValueError as e:
       print(f"Error: {e}")  # Error: Cannot unwrap a Nothing

**Best Practice:** Only unwrap at the edges of your program. Keep values wrapped in ``Maybe`` as long as possible.

Step 6: Practical Example
--------------------------

Let's write a function that safely divides two numbers:

.. code-block:: python

   from katharos.types import Maybe

   def safe_divide(a: float, b: float) -> Maybe[float]:
       """Safely divide a by b, returning Nothing if b is zero."""
       if b == 0:
           return Maybe.Nothing()
       return Maybe.Just(a / b)

   # Use the function
   result1 = safe_divide(10, 2)
   print(result1)  # Just(5.0)

   result2 = safe_divide(10, 0)
   print(result2)  # Nothing()

   # Chain operations
   result3 = safe_divide(10, 2).fmap(lambda x: x * 3)
   print(result3)  # Just(15.0)

   result4 = safe_divide(10, 0).fmap(lambda x: x * 3)
   print(result4)  # Nothing() - function never called!

What You've Learned
-------------------

Congratulations! You've learned:

- ✅ How to install Katharos
- ✅ How to create ``Maybe`` values with ``Just`` and ``Nothing``
- ✅ How to map functions over ``Maybe`` using ``fmap``
- ✅ How to chain operations safely
- ✅ How to extract values with ``unwrap``
- ✅ How to write safe functions that return ``Maybe``

Next Steps
----------

- Learn about :doc:`first-monad` to understand monadic operations
- Explore :doc:`error-handling` with the ``Result`` type
- Check out :doc:`functor-pipeline` for more advanced composition

Further Reading
---------------

- :class:`katharos.types.Maybe` - API reference
- :doc:`../explanation/fp-concepts` - Understanding functional programming
- :doc:`../how-to/chain-operations` - Advanced chaining patterns
