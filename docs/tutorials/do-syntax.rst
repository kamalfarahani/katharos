Combining Multiple Monadic Values with Do Syntax
==================================================

In this tutorial, we will build a script that combines several ``Maybe`` values into a single result through a multi-argument plain function. Along the way, we will encounter the ``@do`` decorator, the ``DoBlock`` return type, and see how bound values are available immediately for use in subsequent steps — without any placeholder workarounds.

Prerequisites
-------------

- Complete the :doc:`monadic-computation` tutorial so you are familiar with ``|`` (bind) and ``Maybe[T].ret``.

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
               lambda z: Maybe[float].ret(process(x, y, z))
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

Now, we replace the nested bind block with a ``@do`` decorated generator. Add a new import at the top of the file:

.. code-block:: python

   from katharos.syntax_sugar import do, DoBlock

Then replace the entire ``result = ...`` block from Step 2 with:

.. code-block:: python

   @do(Maybe)
   def block() -> DoBlock[float]:
       x: float = yield m1
       y: float = yield m2
       z: float = yield m3
       return process(x, y, z)

   result = block()
   print(result)

Run the file. The output should look like this:

.. code-block:: text

   Just(23.0)

Notice three things:

- The result is identical to Step 2.
- ``@do(Maybe)`` tells the decorator which monad this block works with. Every ``yield`` must produce a value of that monad type.
- ``DoBlock[float]`` is the return type annotation for the generator. The type argument — ``float`` here — is the type of the plain value returned by the block. The decorator lifts it into the monad automatically.

Notice also that each ``yield`` expression evaluates to ``Any`` at runtime from Python's perspective — the language cannot track different inner types across multiple ``yield`` sites in the same generator. Write the type of each bound value inline, as shown with ``x: float = yield m1``, to let your type checker and readers know what to expect.

Step 4: Use a Bound Value in a Subsequent Yield
------------------------------------------------

Unlike the old context-manager API, ``yield`` gives you the real unwrapped value immediately. You can use it in the very next line — including passing it to another monadic function. Replace the ``block`` definition with:

.. code-block:: python

   @do(Maybe)
   def block() -> DoBlock[float]:
       x: float = yield m1
       x_scaled: float = yield Maybe[float].Just(x * 3)  # x is 2.0 here
       y: float = yield m2
       z: float = yield m3
       return process(x_scaled, y, z)

   result = block()
   print(result)

Run the file. The output should look like this:

.. code-block:: text

   Just(25.0)

Notice that ``x`` on the second line is the real number ``2.0``, not a placeholder. We multiplied it by ``3`` and wrapped the result in a new ``Maybe`` before yielding — something impossible with a placeholder-based API. The computation is ``(2.0 * 3) * 2 + 3.0 + 4.0 ** 2 = 25.0``.

Now restore ``block`` to the simpler version from Step 3 before continuing:

.. code-block:: python

   @do(Maybe)
   def block() -> DoBlock[float]:
       x: float = yield m1
       y: float = yield m2
       z: float = yield m3
       return process(x, y, z)

Step 5: Watch the Block Short-Circuit
--------------------------------------

Now, we change one of the inputs to ``Nothing()`` to see what happens when any value is missing. Change ``m2`` to:

.. code-block:: python

   m2 = Maybe[float].Nothing()

Run the file. The output should look like this:

.. code-block:: text

   Nothing()

Notice that ``process`` was never called. As soon as any ``yield`` step receives ``Nothing()``, the whole block short-circuits, exactly like a chain of ``|``.

Step 6: Yield a Step That Itself Returns a Maybe
-------------------------------------------------

Finally, we add a transformation step whose own result is a ``Maybe``. With the ``@do`` decorator, there is no special handling needed: if a function already returns a ``Maybe``, just ``yield`` its result directly. First, restore ``m2`` and add a new function and input:

.. code-block:: python

   m2 = Maybe[float].Just(3.0)

   def safe_sqrt(x: float) -> Maybe[float]:
       if x < 0:
           return Maybe[float].Nothing()
       return Maybe[float].Just(x ** 0.5)

   raw = Maybe[float].Just(16.0)

Then replace ``block`` with:

.. code-block:: python

   @do(Maybe)
   def block() -> DoBlock[float]:
       r: float = yield raw
       x: float = yield safe_sqrt(r)  # safe_sqrt returns Maybe[float] — just yield it
       y: float = yield m2
       z: float = yield m3
       return process(x, y, z)

   result = block()
   print(result)

Run the file. The output should look like this:

.. code-block:: text

   Just(27.0)

Notice the value flow: ``raw = 16.0``, ``safe_sqrt(16.0) = 4.0``, then ``process(4.0, 3.0, 4.0) = 4.0*2 + 3.0 + 4.0**2 = 27.0``. Because ``safe_sqrt`` already returns a ``Maybe``, we ``yield`` its result directly and the bind chain takes care of the rest — no distinction between "plain return" and "monadic return" is needed.

What We Built
-------------

We built a script that:

- Uses ``@do(Maybe)`` to declare which monad the block works with.
- Uses ``DoBlock[float]`` to declare the plain return type of the block.
- Binds each monadic input to a real value with ``yield``, annotating the type inline.
- Uses bound values immediately in subsequent ``yield`` expressions.
- Returns a plain value that the decorator lifts into the monad automatically.
- Short-circuits to ``Nothing()`` as soon as any input is missing.
- Passes a ``Maybe``-returning function's result straight to ``yield`` without any wrapping distinction.
