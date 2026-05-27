Why Functional Programming in Python?
=====================================

Python is a multiparadigm language. You can write it imperatively, in an
object-oriented style, or functionally — and most real codebases mix all
three. So why would you reach for a library like Katharos at all? What
problems does it actually solve?

The short answer is that functional programming in Python is primarily
about *making failure and uncertainty visible in the type system* rather
than hiding them behind runtime surprises. To understand why that matters,
it helps to look at the three pain points that motivate the approach.

The Three Problems
------------------

**1. None propagates silently**

``None`` is everywhere in Python. A dictionary lookup returns ``None``.
A database query returns ``None``. An optional configuration value is
``None``. And because the type system treats ``Optional[str]`` and ``str``
identically at runtime, there is nothing stopping you from passing a
``None`` into a function that expects a real string.

The result is a class of bugs that look like this::

   # user_service.py
   def get_username(user_id: int) -> str:
       user = db.find(user_id)
       return user.name          # AttributeError if user is None

   # somewhere else, later
   greeting = "Hello, " + get_username(42).upper()  # crash here

The crash does not happen where ``None`` originates. It happens two or
three calls later, at a place that had no reason to expect a missing value.
The type annotation ``-> str`` was a lie, and the type checker had no way
to know it was a lie.

**2. Exceptions are invisible contracts**

Python exceptions are unchecked. A function's signature tells you what it
returns when it succeeds, but says nothing about what it raises when it
fails::

   def parse_config(path: str) -> Config:
       ...

Does this raise ``FileNotFoundError``? ``PermissionError``? ``ValueError``?
``json.JSONDecodeError``? You have to read the implementation — or discover
it at runtime — to find out. Callers routinely forget to handle failures,
not out of carelessness, but because the signature gave them no reason to
think a failure was possible.

**3. Side effects are unconstrained**

A pure function maps inputs to outputs and does nothing else. But Python
functions can do anything: read files, write to a database, mutate global
state, send HTTP requests. There is no syntactic or type-level signal to
distinguish a function that transforms a string from one that writes to
disk.

This makes functions hard to test in isolation, hard to reason about, and
hard to compose — because you cannot call a function without potentially
triggering some externally observable action.

The Functional Approach
-----------------------

Each of these problems has a functional solution, and each solution works
by moving the problem from the runtime into the type signature.

**Maybe makes absence explicit**

Instead of ``Optional[str]``, which is ``str | None`` at the type level
but indistinguishable at runtime, ``Maybe[str]`` forces every caller to
acknowledge that the value might not be there::

   from katharos.types import Maybe

   def find_user(user_id: int) -> Maybe[str]:
       ...

Now the return type says, unambiguously: *this might not have a value*. You
cannot use the result as a plain string — you must either unwrap it
explicitly (checking ``is_just()`` first), transform it with ``fmap``, or
chain it with ``|``. The type checker enforces this. A missing value cannot
propagate silently through the codebase, because the type carries the
uncertainty at every step.

**Result makes failure explicit**

``Result[E, A]`` encodes the possibility of failure directly in the return
type::

   from katharos.types import Result

   def parse_config(path: str) -> Result[Exception, Config]:
       ...

The caller cannot ignore the error case. They either handle it, propagate
it with ``|``, or consciously call ``.unwrap()`` and accept the risk. More
importantly, this composes: a pipeline of ``Result``-returning functions
chains with ``|``, and the first failure short-circuits the rest — no
``try/except`` needed at each step, no missed error handling.

**IO makes side effects explicit**

``IO[A]`` wraps a computation that produces a value *and* has a side
effect. The side effect does not happen when you build the ``IO`` value —
it only happens when you call ``.execute()``::

   from katharos.types import IO

   def log_result(value: str) -> IO[str]:
       ...

A function that returns ``IO[A]`` is advertising: *I have a side effect.*
This lets you build and compose a pipeline of actions without triggering
any of them, and then run the whole thing at one explicit point.

Why Python Specifically?
------------------------

Python's type hint system (PEP 484 and later) is what makes this practical.
Without Pyright or mypy, ``Maybe[str]`` is just a class you could ignore.
With a type checker enforcing it, the compile-time guarantees are real.

Python is also genuinely multiparadigm. You do not have to convert an
entire codebase to adopt these patterns. You can introduce ``Maybe`` in the
parts of your code that deal with optional lookups, keep ``try/except``
where it is the right tool, and use plain functions everywhere else.
Katharos does not require you to go all-in.

The Trade-offs
--------------

This approach is not free.

**It is unfamiliar.** Most Python developers are not used to working with
``Maybe`` and ``Result``. The learning curve is real, and the value is not
obvious until you have been bitten by a ``None`` propagation bug or a
silently swallowed exception.

**It is more verbose in simple cases.** ``Maybe[str].Just("hello")`` is
more to write than ``"hello"``. For simple scripts or one-off code, this
overhead is not worth it.

**Python was not designed for this.** Haskell, Elm, and Rust have deep
language-level support for these patterns — pattern matching, algebraic
data types, exhaustiveness checking. Python's equivalent features are more
recent (structural pattern matching arrived in 3.10) and less ergonomic.
You are working slightly against the grain of the language.

**The gains compound with scale.** The value of explicit ``Maybe`` and
``Result`` types is low in a 50-line script and high in a 50-module
codebase with many contributors. The larger and longer-lived the project,
the more the upfront investment pays off.

When It Is Worth It
-------------------

Katharos makes the most sense when:

- Functions in your domain regularly produce values that may or may not
  exist, and the missing case has to be handled everywhere it propagates.
- Errors in your system are expected, varied, and composable — not just
  exceptional crashes.
- You want to push side effects to the edges of your application and keep
  the core logic pure and testable.
- Your type checker is part of your development workflow, so the
  compile-time guarantees are actually enforced.

If your codebase is a short script, a quick prototype, or an area where
Python's existing idioms work cleanly, the overhead is probably not
justified. Use the right tool for the context.

Further Reading
---------------

- :doc:`../tutorials/handling-null` — build a program using ``Maybe``
  without writing a single ``None`` check
- :doc:`../tutorials/error-handling` — see ``Result`` handle cascading
  failures in a validation pipeline
- :doc:`../tutorials/io` — defer and sequence side effects with ``IO``
