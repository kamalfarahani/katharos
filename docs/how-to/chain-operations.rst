How to Chain Monadic Operations
================================

This guide shows you how to chain ``Maybe`` and ``Result`` operations using the ``|`` bind operator so that each step in a pipeline receives the unwrapped value from the previous step and the chain short-circuits automatically on failure.

Prerequisites
-------------

- ``katharos`` installed (``pip install katharos`` or ``uv add katharos``)
- Familiarity with ``Maybe.Just`` / ``Maybe.Nothing`` and ``Result.Success`` / ``Result.Failure``

Chaining with Maybe
--------------------

Use ``|`` to pass the unwrapped value of a ``Just`` into the next function. If any step returns ``Nothing()``, all subsequent steps are skipped.

.. code-block:: python

   from katharos.types import Maybe

   def parse_int(s: str) -> Maybe[int]:
       try:
           return Maybe.Just(int(s))
       except ValueError:
           return Maybe.Nothing()

   def reciprocal(n: int) -> Maybe[float]:
       if n == 0:
           return Maybe.Nothing()
       return Maybe.Just(1.0 / n)

   def percent(x: float) -> Maybe[str]:
       return Maybe.Just(f"{x * 100:.1f}%")

   result = (
       parse_int("4")
       | reciprocal
       | percent
   )
   # result == Just('25.0%')

   missing = (
       parse_int("0")
       | reciprocal      # returns Nothing() here
       | percent         # skipped
   )
   # missing == Nothing()

Each function in the chain must accept a plain value and return a ``Maybe``. The ``|`` operator unwraps the ``Just`` before calling the next function; on ``Nothing()`` it bypasses all remaining steps.

Chaining with Result
---------------------

``Result`` follows the same pattern. A ``Failure`` short-circuits the chain and carries the original exception through to the end.

.. code-block:: python

   from katharos.types import Result

   def parse_float(s: str) -> Result[Exception, float]:
       try:
           return Result.Success(float(s))
       except ValueError as e:
           return Result.Failure(e)

   def safe_sqrt(x: float) -> Result[Exception, float]:
       if x < 0:
           return Result.Failure(ValueError(f"Cannot take sqrt of {x}"))
       return Result.Success(x ** 0.5)

   def to_two_dp(x: float) -> Result[Exception, str]:
       return Result.Success(f"{x:.2f}")

   result = (
       parse_float("16.0")
       | safe_sqrt        # 4.0
       | to_two_dp        # "4.00"
   )
   # result == Success('4.00')

   bad = (
       parse_float("abc")   # Failure(ValueError(...))
       | safe_sqrt          # skipped
       | to_two_dp          # skipped
   )
   # bad == Failure(ValueError("could not convert string to float: 'abc'"))

Accessing the final value
--------------------------

Call ``.unwrap()`` on a ``Just`` or ``Success`` to get the inner value when you are ready to leave the functional pipeline:

.. code-block:: python

   value = result.unwrap()  # '4.00'

Check the state before unwrapping when the result may be a failure:

.. code-block:: python

   if result.is_success():
       print(result.unwrap())
   else:
       print(f"Error: {result.error}")

Mixing ``fmap`` and ``|``
--------------------------

Use ``fmap`` when a step cannot fail (the transform always produces a value). Use ``|`` when the step itself might return ``Nothing`` or ``Failure``.

.. code-block:: python

   result = (
       parse_float("9.0")
       | safe_sqrt                          # fallible — use |
       .fmap(lambda x: round(x, 3))        # infallible — use fmap
       | to_two_dp                          # fallible — use |
   )

.. note::

   ``fmap`` wraps the return value automatically, so a function passed to ``fmap`` should return a plain value, not a ``Maybe`` or ``Result``. Passing a monadic-returning function to ``fmap`` nests the container — use ``|`` instead.
