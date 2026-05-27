Sequencing Side Effects with IO
================================

In this tutorial, we will build a data processing script that defers all of its console output until the very end of the computation. Along the way, we will encounter ``IO``, ``FunctionWithSideEffect``, ``fmap``, and the ``>>`` operator for sequencing side effects.

Prerequisites
-------------

- Python 3.13 or later
- Katharos installed (see :doc:`getting-started`)
- Complete the :doc:`monadic-computation` tutorial so you are familiar with ``fmap`` and ``|``

Step 1: Create a Pure IO Value
-------------------------------

Create a new file called ``audit.py`` with the following contents:

.. code-block:: python

   from katharos.types.side_effect import IO

   score = IO(0)
   print(score.value)
   score.execute()
   print("execute() returned")

Run the file:

.. code-block:: bash

   python audit.py

You should see:

.. code-block:: text

   0
   execute() returned

Notice that ``execute()`` ran without printing anything. A plain ``IO(value)`` holds a value but has no side effect attached to it.

Step 2: Transform the Value with fmap
--------------------------------------

Now we will apply a transformation to the value inside ``IO``. Replace the contents of ``audit.py`` with:

.. code-block:: python

   from katharos.types.side_effect import IO

   score = IO(10)
   doubled = score.fmap(lambda x: x * 2)
   print(doubled.value)

Run the file:

.. code-block:: bash

   python audit.py

You should see:

.. code-block:: text

   20

Notice that ``fmap`` transforms the value and returns a new ``IO``. No side effects are involved.

Step 3: Attach a Side Effect
------------------------------

Now we will create an ``IO`` that also prints a log message when executed. Replace the contents of ``audit.py`` with:

.. code-block:: python

   from katharos.types.side_effect import IO, FunctionWithSideEffect

   score = IO(
       10,
       FunctionWithSideEffect(f=lambda: print("Score recorded: 10")),
   )

   print(score.value)
   print("About to execute...")
   score.execute()

Run the file:

.. code-block:: bash

   python audit.py

You should see:

.. code-block:: text

   10
   About to execute...
   Score recorded: 10

Notice that the print statement only appeared after ``execute()`` was called. The ``FunctionWithSideEffect`` stores the action; it does not run it immediately.

Step 4: Sequence Two IO Actions with ``>>``
-------------------------------------------

Now we will chain two ``IO`` actions together so both of their side effects run in order. Replace the contents of ``audit.py`` with:

.. code-block:: python

   from katharos.types.side_effect import IO, FunctionWithSideEffect

   step1 = IO(
       10,
       FunctionWithSideEffect(f=lambda: print("Step 1: initial score = 10")),
   )
   step2 = IO(
       20,
       FunctionWithSideEffect(f=lambda: print("Step 2: doubled score = 20")),
   )

   pipeline = step1 >> step2

   print(f"Final value: {pipeline.value}")
   print("Running side effects:")
   pipeline.execute()

Run the file:

.. code-block:: bash

   python audit.py

You should see:

.. code-block:: text

   Final value: 20
   Running side effects:
   Step 1: initial score = 10
   Step 2: doubled score = 20

Notice two things:

- ``pipeline.value`` is ``20`` — the value from the *second* ``IO``. The ``>>`` operator keeps the value of the right-hand side and discards the value of the left-hand side.
- Both side effects ran in order when ``execute()`` was called, even though step1's value was discarded.

Step 5: Build a Complete Audit Pipeline
-----------------------------------------

Now we will build a three-step pipeline that logs each processing step and executes the entire audit log at the end. Replace the contents of ``audit.py`` with:

.. code-block:: python

   from katharos.types.side_effect import IO, FunctionWithSideEffect

   initial = 10

   step1 = IO(
       initial,
       FunctionWithSideEffect(f=lambda: print(f"[AUDIT] Received score: {initial}")),
   )

   doubled = initial * 2
   step2 = IO(
       doubled,
       FunctionWithSideEffect(f=lambda: print(f"[AUDIT] Doubled score: {doubled}")),
   )

   bonus = doubled + 5
   step3 = IO(
       bonus,
       FunctionWithSideEffect(f=lambda: print(f"[AUDIT] Added bonus: {bonus}")),
   )

   pipeline = step1 >> step2 >> step3

   print(f"Final score: {pipeline.value}")
   print("--- Audit log ---")
   pipeline.execute()

Run the file:

.. code-block:: bash

   python audit.py

You should see:

.. code-block:: text

   Final score: 25
   --- Audit log ---
   [AUDIT] Received score: 10
   [AUDIT] Doubled score: 20
   [AUDIT] Added bonus: 25

Notice that all three audit entries appeared together under the "Audit log" heading, not scattered across the computation. The ``>>`` operator accumulated all three side effects into a single ``IO`` that we executed once at the end.

If your audit log is missing entries, you have probably forgotten to connect a step with ``>>`` or forgotten to call ``execute()``.

What We Built
-------------

We built a data processing script where all side effects are deferred and collected into a single ``IO`` using ``>>``. Calling ``execute()`` once at the end runs every accumulated side effect in the order they were chained. The computation itself (values) and the observable output (side effects) are kept completely separate.
