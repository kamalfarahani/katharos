Errors as Values: ``catch`` and Traceback Preservation
======================================================

Katharos models failure as a *value* - a ``Result`` that is either a ``Success``
or a ``Failure`` - rather than as control flow that unwinds the stack. This
article explains why ``Result.catch`` exists, why it is shaped as a decorator
factory, and why it goes out of its way to preserve the original exception's
traceback.

Exceptions as values, not control flow
--------------------------------------

In ordinary Python, a failure is an event: an exception is raised, the current
call stack unwinds, and execution jumps to whichever ``try/except`` happens to
be waiting up the stack. The function's signature says nothing about this -
``def parse_config(path: str) -> Config`` gives no hint that it might raise
``FileNotFoundError`` or ``ValueError``. The possibility of failure is invisible
until it happens at runtime.

The functional approach makes failure part of the return type instead.
``Result[E, A]`` says, in the signature, *this computation may fail with an error
of type* ``E``. The caller cannot accidentally ignore it: they must handle the
failure, propagate it with ``|``, or consciously call ``.unwrap()``. Failure
becomes a value you pass around and compose, not an exception you hope someone
catches.

Why a decorator factory
-----------------------

A great deal of Python code already raises exceptions - the standard library,
third-party packages, your own existing functions. ``Result.catch`` is the
bridge between that world and the errors-as-values world. Rather than hand-write
the same ``try/except`` wrapper at every boundary:

.. code-block:: python

   def parse_int(s: str) -> Result[ValueError, int]:
       try:
           return Result.Success(int(s))
       except ValueError as e:
           return Result.Failure(e)

you declare the exception you expect and let ``catch`` generate the wrapper:

.. code-block:: python

   @Result.catch(ValueError)
   def parse_int(s: str) -> int:
       return int(s)

The decorator-factory shape - ``catch(ExceptionType)`` returns a decorator - is
what lets you name the exception type at the call site. That choice carries two
deliberate design decisions:

- **Selective catching.** Only the declared type (and its subclasses) becomes a
  ``Failure``. Every other exception propagates untouched. This keeps ``catch``
  from swallowing bugs: a ``ValueError`` you expected becomes a value, but an
  unexpected ``TypeError`` from a genuine programming error still crashes loudly,
  the way it should.
- **Composability.** The wrapped function returns a plain ``Result``, so it slots
  into the same ``fmap`` / ``bind`` / ``|`` pipelines as everything else in the
  library. ``catch`` does not introduce a new kind of value to special-case; it
  lifts existing functions into the type you already use.

Why preserving the traceback matters
------------------------------------

The usual objection to errors-as-values is that you lose the debugging
information a traceback gives you. When you catch an exception and replace it
with, say, a string message or a custom error code, the stack - the precise line
that failed - is gone.

``catch`` avoids this. It stores the *original exception instance* in the
``Failure``; it does not re-raise it, wrap it in a new exception, or reduce it to
a message. When Python raises an exception, it attaches the traceback to that
instance as ``__traceback__``, and because ``catch`` keeps the instance intact,
the traceback travels with it:

.. code-block:: python

   import traceback

   result = parse_int("bad")
   if result.is_failure():
       traceback.print_exception(result.error)        # shows the failing line
       frames = traceback.format_tb(result.error.__traceback__)

This is the point: you get the *discipline* of errors-as-values - failure visible
in the type, impossible to ignore, composable with the rest of your pipeline -
*without* giving up the *debuggability* of exceptions. The failing line is still
recoverable, just from a value you chose when to inspect rather than from a stack
unwind you had to catch in the right place.

The trade-off
-------------

``catch`` is the right tool when the failures are expected and you want to handle
them as data: parsing, I/O, validation, anything where "this might fail" is part
of the normal flow. It is not a replacement for letting genuine bugs crash -
which is exactly why it catches only the type you name. Use it to convert the
exceptions you anticipate into values, and let everything else propagate.

Further reading
---------------

- :doc:`why-fp-in-python` - the broader case for making failure and absence
  explicit in the type system
- :doc:`../how-to/catch-exceptions` - practical recipes for using ``Result.catch``
- :doc:`../tutorials/error-handling` - build a validation pipeline with ``Result``
