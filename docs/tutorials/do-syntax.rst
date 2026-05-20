Combining Multiple Monadic Values with Do Syntax
==================================================

In this tutorial, we will take a plain function with **three arguments** and feed it values that live inside ``Maybe``. We will first do it the hard way (nested bind lambdas) and then rewrite it with do syntax. By the end, we will have a single Python script that combines several monadic values into one result, cleanly and readably.

Prerequisites
-------------

- Complete the :doc:`monadic-computation` tutorial so you are familiar with ``|`` (bind) and ``Maybe.ret``.

Step 1: Create the Script and a Multi-Argument Function
--------------------------------------------------------

First, we create a new file called ``combine.py`` and add a plain function that takes three numbers, plus three monadic inputs:

.. code-block:: python

   from katharos.types import Maybe

   def process(x: float, y: float, z: float) -> float:
       return x * 2 + y + z ** 2

   m1 = Maybe[float].Just(2.0)
   m2 = Maybe[float].Just(3.0)
   m3 = Maybe[float].Just(4.0)

   print(m1, m2, m3)

Now, run the file:

.. code-block:: bash

   python combine.py

The output should look like this:

.. code-block:: text

   Just(2.0) Just(3.0) Just(4.0)

Notice the values we want to feed into ``process`` are wrapped in ``Maybe`` and cannot be passed in directly.

Step 2: Combine Them with Nested Bind
--------------------------------------

Next, we use ``|`` (bind) to unwrap each value and pass it to ``process``. Replace the ``print`` line with:

.. code-block:: python

   result = m1 | (
       lambda x: m2 | (
           lambda y: m3 | (
               lambda z: Maybe.ret(process(x, y, z))
           )
       )
   )
   print(result)

Run the file again. The output should look like this:

.. code-block:: text

   Just(23.0)

It works (``2*2 + 3 + 4**2 = 23``), but notice the problem: each new monadic input adds another nested lambda. With three inputs we already have three levels of indentation, and the data flow is buried inside the lambda parameters.

Step 3: Rewrite the Same Logic with Do Syntax
----------------------------------------------

Now, we replace the nested bind block with a ``Do`` block. Add a new import at the top of the file:

.. code-block:: python

   from katharos.syntax_sugar import Do

Then replace the entire ``result = ...`` block from Step 2 with:

.. code-block:: python

   with Do[Maybe]() as do:
       x = do.arrow(m1)
       y = do.arrow(m2)
       z = do.arrow(m3)
       result = do.ret(process, x=x, y=y, z=z)

   print(result)

Run the file. The output should look like this:

.. code-block:: text

   Just(23.0)

Notice three things:

- The result is identical to Step 2.
- Each monadic input is unwrapped on its own line with ``do.arrow``.
- ``do.ret`` calls our plain ``process`` function with the unwrapped values and wraps the final answer back into ``Maybe`` for us.

Step 4: Discover the DoVariable Pitfall
----------------------------------------

It is tempting to use ``x``, ``y``, ``z`` as if they were ordinary numbers, but ``do.arrow`` does **not** return the unwrapped value — it returns a ``DoVariable`` placeholder that only stands in for the value while the block is being assembled.

Let's see what happens when we treat a placeholder like a real number. Replace the ``Do`` block from Step 3 with:

.. code-block:: python

   with Do[Maybe]() as do:
       x = do.arrow(m1)
       y = do.arrow(m2)
       z = do.arrow(m3)
       print("x is:", x)
       result = do.ret(lambda: process(x + 1, y, z))

   print(result)

Run the file. The output should look like this:

.. code-block:: text

   x is: DoVariable(index=0, monad=Just(2.0))
   Traceback (most recent call last):
     ...
   TypeError: unsupported operand type(s) for +: 'DoVariable' and 'int'

Notice two things:

- ``x`` is a ``DoVariable``, not the number ``2.0``. You cannot do arithmetic on it, index it, or call methods on the value it represents.
- The fix is always the same: hand placeholders to ``do.ret`` / ``do.eval`` as **keyword arguments**, and let the framework pass the unwrapped values into your function.

Now, restore the working version from Step 3 before continuing:

.. code-block:: python

   with Do[Maybe]() as do:
       x = do.arrow(m1)
       y = do.arrow(m2)
       z = do.arrow(m3)
       result = do.ret(process, x=x, y=y, z=z)

   print(result)

Step 5: Watch the Block Short-Circuit
--------------------------------------

Now, we change one of the inputs to ``Nothing()`` to see what happens when any value is missing. Change ``m2`` to:

.. code-block:: python

   m2 = Maybe.Nothing()

Run the file. The output should look like this:

.. code-block:: text

   Nothing()

Notice that ``process`` was never called. As soon as any ``do.arrow`` step yields ``Nothing()``, the whole block short-circuits, exactly like a chain of ``|``.

Step 6: Insert a Step That Itself Returns a Maybe
--------------------------------------------------

Finally, we add a transformation step whose own result is a ``Maybe``. For that we use ``do.eval`` (instead of ``do.ret``) so the result is **not** wrapped a second time. First, restore ``m2`` and add a new function and input:

.. code-block:: python

   m2 = Maybe.Just(3.0)

   def safe_sqrt(x: float) -> Maybe[float]:
       if x < 0:
           return Maybe.Nothing()
       return Maybe.Just(x ** 0.5)

   raw = Maybe.Just(16.0)

Then replace the ``Do`` block with:

.. code-block:: python

   with Do[Maybe]() as do:
       r = do.arrow(raw)
       x = do.arrow(do.eval(safe_sqrt, x=r))
       y = do.arrow(m2)
       z = do.arrow(m3)
       result = do.ret(process, x=x, y=y, z=z)

   print(result)

Run the file. The output should look like this:

.. code-block:: text

   Just(27.0)

Notice the value flow: ``raw = 16``, ``safe_sqrt(16) = 4``, then ``process(4, 3, 4) = 4*2 + 3 + 4**2 = 27``. We used ``do.eval`` for ``safe_sqrt`` because it already returns a ``Maybe``; using ``do.ret`` there would have produced ``Just(Just(4.0))``.

What We Built
-------------

We built a script that:

- Combines several monadic values into a single result through a multi-argument plain function.
- Uses ``do.arrow`` to unwrap each input on its own line.
- Uses ``do.ret`` to lift a plain function's result back into the monad.
- Uses ``do.eval`` to call a function that already returns a monad without double-wrapping.
- Short-circuits to ``Nothing()`` as soon as any input is missing.
- Treats ``do.arrow`` results as ``DoVariable`` placeholders, never as real values.
