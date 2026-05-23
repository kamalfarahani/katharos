How to Use Do-Notation
======================

This guide shows you how to use ``Do[M]`` to combine several monadic values in a readable, imperative style — without writing nested lambda chains.

Prerequisites
-------------

- Familiarity with the ``|`` bind operator (see :doc:`chain-operations`)
- The monad type you want to use (``Maybe``, ``Result``, ``IO``, etc.)

Basic structure
---------------

A do-block has three parts: entering the context, binding values with ``do.arrow``, and returning a result with ``do.ret`` or ``do.eval``.

.. code-block:: python

   from katharos.syntax_sugar import Do
   from katharos.types import Maybe

   with Do[Maybe]() as do:
       x = do.arrow(Maybe.Just(10))
       y = do.arrow(Maybe.Just(5))
       result = do.ret(lambda x, y: x + y, x=x, y=y)

   # result == Just(15)

- ``do.arrow(m)`` — registers the monadic value ``m`` and returns a placeholder variable. This is the ``<-`` of Haskell do-notation.
- ``do.ret(f, **vars)`` — calls ``f`` with the unwrapped values and wraps the plain return value back into the monad.
- ``do.eval(f, **vars)`` — like ``do.ret`` but ``f`` already returns a monadic value; no re-wrapping is done.

Short-circuit behaviour
-----------------------

When any ``do.arrow`` step holds a ``Nothing()`` or ``Failure``, the entire block short-circuits and the final variable holds that failure:

.. code-block:: python

   with Do[Maybe]() as do:
       x = do.arrow(Maybe.Just(10))
       y = do.arrow(Maybe.Nothing())   # short-circuits here
       result = do.ret(lambda x, y: x + y, x=x, y=y)

   # result == Nothing()

Using do.eval for monadic return values
---------------------------------------

Use ``do.eval`` when the final function itself returns a ``Maybe`` or ``Result`` — for example when it calls another fallible function:

.. code-block:: python

   def lookup(key: str) -> Maybe[str]:
       db = {"alice": "admin", "bob": "user"}
       return Maybe.Just(db[key]) if key in db else Maybe.Nothing()

   def greet(role: str) -> Maybe[str]:
       if role == "admin":
           return Maybe.Just("Hello, Admin!")
       return Maybe.Nothing()

   with Do[Maybe]() as do:
       role   = do.arrow(lookup("alice"))
       result = do.eval(greet, role=role)   # greet already returns Maybe

   # result == Just('Hello, Admin!')

Using with Result
-----------------

The same pattern works with ``Result``:

.. code-block:: python

   from katharos.types import Result

   def parse_int(s: str) -> Result[Exception, int]:
       try:
           return Result.Success(int(s))
       except ValueError as e:
           return Result.Failure(e)

   def safe_divide(a: int, b: int) -> Result[Exception, float]:
       if b == 0:
           return Result.Failure(ZeroDivisionError("division by zero"))
       return Result.Success(a / b)

   with Do[Result]() as do:
       a      = do.arrow(parse_int("20"))
       b      = do.arrow(parse_int("4"))
       result = do.eval(lambda a, b: safe_divide(a, b), a=a, b=b)

   # result == Success(5.0)

Sequencing without capturing a value
--------------------------------------

Register a monadic value with ``do.arrow`` even when you do not need its unwrapped content — the block will still short-circuit if it fails:

.. code-block:: python

   def validate_positive(n: int) -> Maybe[int]:
       return Maybe.Just(n) if n > 0 else Maybe.Nothing()

   with Do[Maybe]() as do:
       _guard = do.arrow(validate_positive(5))   # must succeed; value unused
       x      = do.arrow(Maybe.Just(100))
       result = do.ret(lambda x: x * 2, x=x)

   # result == Just(200)
