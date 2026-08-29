How to Convert Exception-Throwing Functions to Result
======================================================

This guide shows how to use ``Result.catch`` to turn an ordinary function that
raises exceptions into one that returns a ``Result`` - without writing a
``try/except`` block yourself. It also covers how to recover the exact line that
caused a failure from the captured exception's traceback.

Prerequisites
-------------

- Familiarity with ``Result.Success`` / ``Result.Failure`` and the ``|`` operator
- If you are new to ``Result``, work through the :doc:`../tutorials/error-handling`
  tutorial first, and see :doc:`error-handling` for the manual try/except approach

Wrap a throwing function with a single decorator
------------------------------------------------

``Result.catch`` is a decorator factory. Pass it the exception type you want to
intercept; it returns a decorator that wraps the function so a normal return
value becomes a ``Success`` and a matching exception becomes a ``Failure``:

.. code-block:: python

   from katharos.types import Result

   @Result.catch(ValueError)
   def parse_int(s: str) -> int:
       return int(s)

   print(parse_int("42"))    # Success(42)
   print(parse_int("bad"))   # Failure(ValueError("invalid literal for int() with base 10: 'bad'"))

This replaces the manual boundary code you would otherwise write:

.. code-block:: python

   def parse_int(s: str) -> Result[ValueError, int]:
       try:
           return Result.Success(int(s))
       except ValueError as e:
           return Result.Failure(e)

The decorated function keeps its name and docstring (``catch`` uses
``functools.wraps`` internally), so it behaves like the original everywhere else.

Catch only the declared type; let others propagate
--------------------------------------------------

Only the exception type you name (and its subclasses) is converted to a
``Failure``. Any other exception propagates unchanged, exactly as it would
without the decorator:

.. code-block:: python

   @Result.catch(ValueError)
   def risky(x: int) -> int:
       if x < 0:
           raise TypeError("negative")
       return x

   print(risky(1))    # Success(1)
   risky(-1)          # raises TypeError - NOT caught, not wrapped in a Result

This is deliberate: ``catch`` narrows exception handling to the failures you
expect, while genuine programming errors still surface as exceptions.

Cover a family of exceptions with a base class
----------------------------------------------

Because subclasses are intercepted too, naming a base exception catches all of
its descendants. For example, ``OSError`` covers ``FileNotFoundError``,
``PermissionError``, and the rest of the OS error hierarchy:

.. code-block:: python

   @Result.catch(OSError)
   def read_file(path: str) -> str:
       with open(path) as f:
           return f.read()

   read_file("/nonexistent")
   # Failure(FileNotFoundError(2, 'No such file or directory'))

Chain the result with the rest of your pipeline
-----------------------------------------------

A function decorated with ``catch`` returns an ordinary ``Result``, so it
composes with ``fmap``, ``bind``, and the ``|`` operator like any other. A
failure short-circuits the rest of the chain:

.. code-block:: python

   @Result.catch(ValueError)
   def parse_int(s: str) -> int:
       return int(s)

   print(parse_int("10").fmap(lambda n: n * 2))   # Success(20)
   print(parse_int("bad").fmap(lambda n: n * 2))  # Failure(ValueError(...)) - lambda never runs

   @Result.catch(ZeroDivisionError)
   def reciprocal(n: int) -> float:
       return 1 / n

   # parse, then divide - the first failure wins
   print(parse_int("4") | reciprocal)   # Success(0.25)
   print(parse_int("0") | reciprocal)   # Failure(ZeroDivisionError('division by zero'))

Recover the line that caused the failure
----------------------------------------

``catch`` stores the *original exception instance* in the ``Failure``, and
Python attaches the traceback to that instance when it is raised. Because the
exception is captured rather than re-raised, its ``__traceback__`` is preserved -
so you can inspect exactly where the failure originated:

.. code-block:: python

   import traceback
   from katharos.types import Result

   @Result.catch(ValueError)
   def parse_int(s: str) -> int:
       return int(s)

   result = parse_int("bad")

   if result.is_failure():
       # Print the full traceback, including the failing line inside parse_int
       traceback.print_exception(result.error)

       # Or format it as a list of frames to log or attach to a report
       frames = traceback.format_tb(result.error.__traceback__)
       print("".join(frames))

This is the key advantage over patterns that discard the stack: you get
errors-as-values *and* keep the debugging information you would have had from a
normal exception.

See also
--------

- :doc:`error-handling` - handle errors with manual ``try/except`` boundaries and
  convert between ``Maybe`` and ``Result``
- :doc:`../explanation/error-handling-and-tracebacks` - why ``catch`` works this
  way and why preserving the traceback matters
