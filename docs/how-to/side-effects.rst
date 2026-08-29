How to Manage Side Effects with ``IO``
======================================

This guide shows you how to use ``IO`` to defer and sequence side-effectful operations - keeping your pure computation separate from I/O until you are ready to execute it.

Prerequisites
-------------

- ``katharos`` installed
- Familiarity with ``fmap`` and the ``|`` bind operator

The core model
--------------

``IO[A]`` wraps a pure value together with a deferred side-effect function. The side effect does not run until you call ``.execute()``.

- ``fmap`` transforms the wrapped value and produces a new ``IO`` with **no side effect**.
- ``|`` (bind) threads the value into the next function **and** merges both side effects, so they execute in order when ``.execute()`` is called.
- ``>>`` (then) sequences two ``IO`` values, discarding the first value but merging both side effects in the same way as ``|``.

Creating an ``IO`` value with a side effect
-------------------------------------------

Use ``FunctionWithSideEffect`` to attach a callable (a function that takes no arguments and returns ``None``) to an ``IO`` value:

.. code-block:: python

   from katharos.types.side_effect import IO, FunctionWithSideEffect

   message = "Processing complete"

   io = IO(
       value=message,
       io_func=FunctionWithSideEffect(f=lambda: print(message)),
   )

   # Nothing has printed yet.
   io.execute()  # prints: Processing complete

Transforming the value without triggering the side effect
----------------------------------------------------------

``fmap`` maps a function over the wrapped value and produces a new ``IO``. The side effect of the original is not carried over:

.. code-block:: python

   io_upper = io.fmap(str.upper)
   # io_upper.value == 'PROCESSING COMPLETE'
   # io_upper has no side effect (FunctionWithSideEffect.no_op())

To transform the value *and* keep the side effect, create a new ``IO`` explicitly:

.. code-block:: python

   upper_value = message.upper()
   io_upper_with_effect = IO(
       value=upper_value,
       io_func=FunctionWithSideEffect(f=lambda: print(upper_value)),
   )

Sequencing multiple ``IO`` actions with ``>>``
----------------------------------------------

``>>`` (the ``then`` operator) sequences two ``IO`` values: it keeps the second value but merges both side effects so they execute in order:

.. code-block:: python

   log_start = IO(
       value=None,
       io_func=FunctionWithSideEffect(f=lambda: print("Starting...")),
   )

   log_end = IO(
       value=42,
       io_func=FunctionWithSideEffect(f=lambda: print("Done. Result:", 42)),
   )

   pipeline = log_start >> log_end
   # pipeline.value == 42

   pipeline.execute()
   # prints:
   # Starting...
   # Done. Result: 42

Building a deferred computation pipeline
-----------------------------------------

Use ``|`` (bind) to thread the value from one ``IO`` into a function that produces the next ``IO``. The side effects accumulate but are not run:

.. code-block:: python

   def compute(x: int) -> IO[int]:
       result = x * 2
       return IO(
           value=result,
           io_func=FunctionWithSideEffect(f=lambda: print(f"computed: {result}")),
       )

   def format_result(x: int) -> IO[str]:
       text = f"answer={x}"
       return IO(
           value=text,
           io_func=FunctionWithSideEffect(f=lambda: print(f"formatted: {text}")),
       )

   initial = IO(value=5, io_func=FunctionWithSideEffect.no_op())

   pipeline = (
       initial
       | compute           # IO(10, prints "computed: 10")
       | format_result     # IO("answer=10", prints "formatted: answer=10")
   )

   # Nothing has run yet.
   print(pipeline.value)   # answer=10
   pipeline.execute()
   # prints:
   # computed: 10
   # formatted: answer=10

Mixing ``fmap`` and ``|`` in the same pipeline
----------------------------------------------

Use ``fmap`` for steps that transform the value but produce no side effect. Use ``|`` for steps that both transform the value and produce a side effect. Both can appear in the same chain:

.. code-block:: python

   def double(x: int) -> int:
       return x * 2

   pipeline = (
       IO.pure(5)
       .fmap(double)           # IO(10) - pure transform, no side effect
       .fmap(double)           # IO(20) - pure transform, no side effect
       | (lambda x: IO(        # side-effectful step
           value=x + 1,
           io_func=FunctionWithSideEffect(f=lambda: print(f"after doubles: {x}")),
       ))
   )

   print(pipeline.value)  # 21
   pipeline.execute()     # prints: after doubles: 20

Checking the value without executing
--------------------------------------

Read ``.value`` to inspect the wrapped result at any time without triggering the side effect:

.. code-block:: python

   pipeline = IO.pure(10).fmap(lambda x: x + 5)
   assert pipeline.value == 15  # no side effect runs
