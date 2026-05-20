Demonstrating Monadic Computations Using Maybe Monad
=====================================

In this tutorial, we will build a small **safe calculation pipeline** that chains operations which can fail, using the bind operator (``|``). By the end, we will have a single Python script that runs a chain of computations and short-circuits cleanly when any step fails.

Prerequisites
-------------

- Complete the :doc:`getting-started` tutorial.
- Complete the :doc:`handling-null` tutorial so you are familiar with ``Maybe.Just`` and ``Maybe.Nothing``.

Step 1: Create the Script and a Failing Function
-------------------------------------------------

First, we create a new file called ``pipeline.py`` and add a function that returns a ``Maybe``:

.. code-block:: python

   from katharos.types import Maybe

   def safe_sqrt(x: float) -> Maybe[float]:
       if x < 0:
           return Maybe.Nothing()
       return Maybe.Just(x ** 0.5)

   print(safe_sqrt(16))
   print(safe_sqrt(-4))

Now, run the file:

.. code-block:: bash

   python pipeline.py

The output should look like this:

.. code-block:: text

   Just(4.0)
   Nothing()

Notice how ``safe_sqrt`` always returns a value wrapped in ``Maybe``.

Step 2: See the Problem with fmap
----------------------------------

Next, we try to apply ``safe_sqrt`` to a value already inside a ``Maybe`` using ``fmap``. Replace the two ``print`` lines with:

.. code-block:: python

   result = Maybe.Just(16).fmap(safe_sqrt)
   print(result)

Run the file again. The output should look like this:

.. code-block:: text

   Just(Just(4.0))

Notice the nested ``Just(Just(...))``. That is the problem we are about to fix.

Step 3: Use Bind to Flatten the Result
---------------------------------------

Now, we replace ``fmap`` with the bind operator ``|``, which is just an infix shorthand for the ``.bind(...)`` method. Change the ``result`` line to:

.. code-block:: python

   result = Maybe.Just(16) | safe_sqrt # or Maybe.Just(16).bind(safe_sqrt)
   print(result)

Run the file again. The output should look like this:

.. code-block:: text

   Just(4.0)

Notice the result is flat. The ``|`` operator applies ``safe_sqrt`` and unwraps the extra layer for us.

Step 4: Chain Two Operations
-----------------------------

Next, we add a second failing function and chain it after ``safe_sqrt``. Add this function below ``safe_sqrt``:

.. code-block:: python

   def safe_reciprocal(x: float) -> Maybe[float]:
       if x == 0:
           return Maybe.Nothing()
       return Maybe.Just(1 / x)

Then replace the ``result`` block with:

.. code-block:: python

   result = Maybe.Just(16) | safe_sqrt | safe_reciprocal
   print(result)

Run the file. The output should look like this:

.. code-block:: text

   Just(0.25)

Notice how the value flows through both steps: ``16 → 4.0 → 0.25``.

Step 5: Watch the Chain Short-Circuit
--------------------------------------

Now, we feed a negative number into the same chain. Change the starting value to ``-16``:

.. code-block:: python

   result = Maybe.Just(-16) | safe_sqrt | safe_reciprocal
   print(result)

Run the file. The output should look like this:

.. code-block:: text

   Nothing()

Notice that ``safe_reciprocal`` was never reached. Once any step returns ``Nothing()``, the rest of the chain is skipped automatically.

Step 6: Start the Chain with ret
---------------------------------

Finally, we use ``Maybe.ret`` to start the chain from a plain value instead of writing ``Maybe.Just`` ourselves. Replace the ``result`` line with:

.. code-block:: python

   result = Maybe.ret(16) | safe_sqrt | safe_reciprocal
   print(result)

Run the file. The output should look like this:

.. code-block:: text

   Just(0.25)

Notice the result is identical to Step 4. ``Maybe.ret`` simply wraps a plain value into the monad so the chain has a starting point.

What We Built
-------------

We built a pipeline that:

- Wraps a starting value with ``Maybe.ret``.
- Chains failure-aware functions with ``|``.
- Produces a flat ``Maybe`` result.
- Short-circuits to ``Nothing()`` as soon as any step fails.
