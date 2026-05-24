How to Use Do-Notation
======================

This guide shows you how to use the ``@do`` decorator to combine several monadic values in a readable, imperative style — without writing nested lambda chains.

Prerequisites
-------------

- Familiarity with the ``|`` bind operator (see :doc:`chain-operations`)
- The monad type you want to use (``Maybe``, ``Result``, ``IO``, etc.)

Basic structure
---------------

A do-block is a generator function decorated with ``@do(M)``. Each ``yield`` extracts the wrapped value; ``return`` produces the plain result, which the decorator lifts into the monad automatically.

.. code-block:: python

   from katharos.syntax_sugar import do, DoBlock
   from katharos.types import Maybe

   @do(Maybe)
   def block() -> DoBlock[int]:
       x: int = yield Maybe[int].Just(10)
       y: int = yield Maybe[int].Just(5)
       return x + y

   block()  # Just(15)

- ``@do(Maybe)`` — declares which monad the block works with. Every ``yield`` must produce a value of that monad type.
- ``DoBlock[int]`` — the return type annotation for the generator. The type argument is the plain return type; the decorator lifts it into the monad.
- ``x: int = yield Maybe[int].Just(10)`` — extracts the wrapped value and binds it to ``x``. Annotate the type inline because Python's ``Generator`` cannot infer per-yield types automatically.

Short-circuit behaviour
-----------------------

When any ``yield`` step holds a ``Nothing()`` or ``Failure``, the entire block short-circuits and the decorator returns that failure immediately:

.. code-block:: python

   @do(Maybe)
   def block() -> DoBlock[int]:
       x: int = yield Maybe[int].Just(10)
       y: int = yield Maybe[int].Nothing()   # short-circuits here
       return x + y

   block()  # Nothing()

Using a bound value in a subsequent yield
-----------------------------------------

Because ``yield`` returns the real unwrapped value — not a placeholder — you can use it immediately in the next line, including passing it to another monadic function:

.. code-block:: python

   def lookup(key: str) -> Maybe[str]:
       db = {"alice": "admin", "bob": "user"}
       return Maybe[str].Just(db[key]) if key in db else Maybe[str].Nothing()

   def greet(role: str) -> Maybe[str]:
       if role == "admin":
           return Maybe[str].Just("Hello, Admin!")
       return Maybe[str].Nothing()

   @do(Maybe)
   def block() -> DoBlock[str]:
       role:   str = yield lookup("alice")
       result: str = yield greet(role)   # role is "admin" here — greet returns Maybe
       return result

   block()  # Just('Hello, Admin!')

When a step already returns a ``Maybe`` (or whichever monad you are using), just ``yield`` its result directly. No special ``eval`` call is needed.

Using with Result
-----------------

The same pattern works with ``Result``:

.. code-block:: python

   from katharos.types import Result

   def parse_int(s: str) -> Result[Exception, int]:
       try:
           return Result[Exception, int].Success(int(s))
       except ValueError as e:
           return Result[Exception, int].Failure(e)

   def safe_divide(a: int, b: int) -> Result[Exception, float]:
       if b == 0:
           return Result[Exception, float].Failure(ZeroDivisionError("division by zero"))
       return Result[Exception, float].Success(a / b)

   @do(Result)
   def block() -> DoBlock[float]:
       a:      int   = yield parse_int("20")
       b:      int   = yield parse_int("4")
       result: float = yield safe_divide(a, b)
       return result

   block()  # Success(5.0)

Sequencing without capturing a value
--------------------------------------

``yield`` a monadic value without assigning the result when you only need the short-circuit behaviour and do not use the unwrapped value:

.. code-block:: python

   def validate_positive(n: int) -> Maybe[int]:
       return Maybe[int].Just(n) if n > 0 else Maybe[int].Nothing()

   @do(Maybe)
   def block() -> DoBlock[int]:
       yield validate_positive(5)       # must succeed; value unused
       x: int = yield Maybe[int].Just(100)
       return x * 2

   block()  # Just(200)
