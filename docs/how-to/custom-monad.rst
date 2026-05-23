How to Implement a Custom Functor, Applicative, and Monad
==========================================================

This guide walks you through implementing a new container type that participates fully in Katharos' algebraic hierarchy. By the end you will have a type that works with ``fmap``, ``**``, ``|``, ``>>`` and ``Do``, with accurate types throughout.

Prerequisites
-------------

- Familiarity with ``Maybe`` or ``Result`` as working examples
- An understanding of what value your new type wraps and what "failure" or "absence" means for it

The hierarchy at a glance
--------------------------

Katharos defines three abstract base classes, each extending the previous:

.. code-block:: text

   Functor     → abstract: fmap
      ↓
   Applicative → abstract: pure (classmethod), ap
                 concrete: ** operator
      ↓
   Monad       → abstract: bind
                 concrete: ret (classmethod), then, | operator, >> operator

Subclassing ``Monad`` requires implementing all four abstract methods: ``fmap``, ``pure``, ``ap``, and ``bind``.

The inherited concrete methods (``ret``, ``then``, ``|``, ``>>``) work at runtime — but due to Python's lack of higher-kinded types, **their return types will be inferred as the abstract base type**, not your concrete type. You must override them with correct return-type annotations to make downstream code type-check properly. This is covered in Step 4.

The example type: Validated
----------------------------

We will build ``Validated[A]``, a container that holds either a valid value or a list of error strings. Unlike ``Result``, which stops at the first failure, ``Validated`` can accumulate errors via ``ap``.

Declare the class using Python's generic syntax. The type parameter workaround ``"Validated[Any]"`` is required because Python has no higher-kinded types — the base class slot for the container type must be filled with a concrete type string:

.. code-block:: python

   from __future__ import annotations
   from collections.abc import Callable
   from typing import Any, cast

   from katharos.algebra import Applicative, Monad

   class Validated[A](
       Monad["Validated[Any]", A]
   ):
       def __init__(
           self,
           value: A | None = None,
           errors: list[str] | None = None,
       ) -> None:
           self._value  = value
           self._errors = errors or []

       @staticmethod
       def Valid(value: A) -> "Validated[A]":
           return Validated(value=value)

       @staticmethod
       def Invalid(*errors: str) -> "Validated[A]":
           return Validated(errors=list(errors))

       def is_valid(self) -> bool:
           return not self._errors

       def __repr__(self) -> str:
           if self.is_valid():
               return f"Valid({self._value!r})"
           return f"Invalid({self._errors!r})"

Step 1 — Implement fmap (Functor)
----------------------------------

Annotate the return type explicitly as ``"Validated[B]"``. Without this, the type checker infers ``Functor[Validated[Any], B]`` — technically correct in the abstract but useless to callers.

After the ``is_valid()`` guard, add ``assert self._value is not None`` so the type checker knows the value is safe to access (the guard narrows the logic but not the type):

.. code-block:: python

   def fmap[B](self, f: Callable[[A], B]) -> "Validated[B]":
       if not self.is_valid():
           return Validated[B].Invalid(*self._errors)
       assert self._value is not None  # type checker narrowing
       return Validated.Valid(f(self._value))

Verify the two functor laws:

.. code-block:: python

   from katharos.functools import F

   v = Validated.Valid(5)

   # Identity law: fmap(id) == id
   assert v.fmap(F.id) == v

   # Composition law: fmap(g . f) == fmap(g)(fmap(f))
   double = lambda x: x * 2
   add1   = lambda x: x + 1
   assert v.fmap(F.compose(add1)(double)) == v.fmap(double).fmap(add1)

Step 2 — Implement pure and ap (Applicative)
---------------------------------------------

**pure**: wrap a plain value into the minimal valid context. Annotate the return as ``"Validated[T]"`` — without it the type checker infers ``Applicative[Validated[Any], T]``:

.. code-block:: python

   @classmethod
   def pure[T](cls, x: T) -> "Validated[T]":
       return Validated.Valid(x)

**ap**: the method signature must use the abstract ``Applicative[...]`` type to satisfy the interface contract. Inside the body, ``cast`` to the concrete type so the type checker understands you can access ``._value`` and ``._errors``:

.. code-block:: python

   def ap[B](
       self,
       wrapped_funcs: Applicative["Validated[Any]", Callable[[A], B]],
   ) -> "Validated[B]":
       wrapped_funcs = cast(Validated[Callable[[A], B]], wrapped_funcs)

       if not self.is_valid() and not wrapped_funcs.is_valid():
           return Validated[B].Invalid(*(self._errors + wrapped_funcs._errors))
       if not wrapped_funcs.is_valid():
           return Validated[B].Invalid(*wrapped_funcs._errors)
       if not self.is_valid():
           return Validated[B].Invalid(*self._errors)

       assert self._value is not None          # type checker narrowing
       assert wrapped_funcs._value is not None # type checker narrowing
       return Validated[B].Valid(wrapped_funcs._value(self._value))

The ``cast`` does not change the runtime value — it only tells the type checker to treat ``wrapped_funcs`` as ``Validated[Callable[[A], B]]`` from that line onwards, enabling access to ``._value`` and ``._errors``.

Verify the homomorphism law:

.. code-block:: python

   f = lambda x: x + 1
   x = 10
   assert Validated.pure(f(x)) == Validated.pure(x) ** Validated.pure(f)

Step 3 — Implement bind and ret (Monad)
-----------------------------------------

**bind**: same pattern as ``ap`` — abstract type in the signature, ``cast`` inside the body, then ``assert`` before access:

.. code-block:: python

   def bind[B](
       self,
       f: Callable[[A], Monad["Validated[Any]", B]],
   ) -> "Validated[B]":
       if not self.is_valid():
           return Validated[B].Invalid(*self._errors)
       f = cast(Callable[[A], Validated[B]], f)
       assert self._value is not None  # type checker narrowing
       return f(self._value)

**ret**: ``Monad.ret`` calls ``pure`` at runtime, so you only need to override it to fix the inferred return type from ``Monad[Validated[Any], T]`` to ``Validated[T]``:

.. code-block:: python

   @classmethod
   def ret[T](cls, x: T) -> "Validated[T]":
       return cls.pure(x)

Verify the monad laws:

.. code-block:: python

   f = lambda x: Validated.Valid(x * 2)
   g = lambda x: Validated.Valid(x + 1)
   v = Validated.Valid(5)

   # Left identity: ret(a).bind(f) == f(a)
   assert Validated.ret(5).bind(f) == f(5)

   # Right identity: m.bind(ret) == m
   assert v.bind(Validated.ret) == v

   # Associativity: m.bind(f).bind(g) == m.bind(lambda x: f(x).bind(g))
   assert v.bind(f).bind(g) == v.bind(lambda x: f(x).bind(g))

Step 4 — Override inherited operators for correct return types
---------------------------------------------------------------

``Monad`` and ``Applicative`` provide ``then``, ``__or__``, ``__rshift__``, and ``__pow__`` — they work at runtime without overriding. But their return types are the abstract base types (``Monad[Validated[Any], B]``, ``Applicative[Validated[Any], B]``), not ``Validated[B]``.

Override each one to annotate the concrete return type. The bodies are one-liners that delegate back to the methods you already implemented:

.. code-block:: python

   def then[B](self, other: Monad["Validated[Any]", B]) -> "Validated[B]":
       return super().then(other)  # type: ignore[return-value]

   def __pow__[B](
       self,
       wrapped_funcs: Applicative["Validated[Any]", Callable[[A], B]],
   ) -> "Validated[B]":
       return self.ap(wrapped_funcs)

   def __or__[B](
       self,
       f: Callable[[A], Monad["Validated[Any]", B]],
   ) -> "Validated[B]":
       return self.bind(f)

   def __rshift__[B](
       self,
       other: Monad["Validated[Any]", B],
   ) -> "Validated[B]":
       return self.then(other)

``then`` is the only one that needs ``# type: ignore[return-value]`` because ``super().then()`` returns ``Monad[Validated[Any], B]`` and there is no way to prove to the type checker at that call site that it is actually ``Validated[B]``.

The complete type
-----------------

.. code-block:: python

   from __future__ import annotations
   from collections.abc import Callable
   from typing import Any, cast

   from katharos.algebra import Applicative, Monad


   class Validated[A](Monad["Validated[Any]", A]):

       def __init__(
           self,
           value: A | None = None,
           errors: list[str] | None = None,
       ) -> None:
           self._value  = value
           self._errors = errors or []

       @staticmethod
       def Valid(value: A) -> "Validated[A]":
           return Validated(value=value)

       @staticmethod
       def Invalid(*errors: str) -> "Validated[A]":
           return Validated(errors=list(errors))

       def is_valid(self) -> bool:
           return not self._errors

       # --- Functor ---
       def fmap[B](self, f: Callable[[A], B]) -> "Validated[B]":
           if not self.is_valid():
               return Validated[B].Invalid(*self._errors)
           assert self._value is not None
           return Validated.Valid(f(self._value))

       # --- Applicative ---
       @classmethod
       def pure[T](cls, x: T) -> "Validated[T]":
           return Validated.Valid(x)

       def ap[B](
           self,
           wrapped_funcs: Applicative["Validated[Any]", Callable[[A], B]],
       ) -> "Validated[B]":
           wrapped_funcs = cast(Validated[Callable[[A], B]], wrapped_funcs)
           if not self.is_valid() and not wrapped_funcs.is_valid():
               return Validated[B].Invalid(*(self._errors + wrapped_funcs._errors))
           if not wrapped_funcs.is_valid():
               return Validated[B].Invalid(*wrapped_funcs._errors)
           if not self.is_valid():
               return Validated[B].Invalid(*self._errors)
           assert self._value is not None
           assert wrapped_funcs._value is not None
           return Validated[B].Valid(wrapped_funcs._value(self._value))

       # --- Monad ---
       @classmethod
       def ret[T](cls, x: T) -> "Validated[T]":
           return cls.pure(x)

       def bind[B](
           self,
           f: Callable[[A], Monad["Validated[Any]", B]],
       ) -> "Validated[B]":
           if not self.is_valid():
               return Validated[B].Invalid(*self._errors)
           f = cast(Callable[[A], Validated[B]], f)
           assert self._value is not None
           return f(self._value)

       # --- Inherited operators, overridden for concrete return types ---
       def then[B](self, other: Monad["Validated[Any]", B]) -> "Validated[B]":
           return super().then(other)  # type: ignore[return-value]

       def __pow__[B](
           self,
           wrapped_funcs: Applicative["Validated[Any]", Callable[[A], B]],
       ) -> "Validated[B]":
           return self.ap(wrapped_funcs)

       def __or__[B](
           self,
           f: Callable[[A], Monad["Validated[Any]", B]],
       ) -> "Validated[B]":
           return self.bind(f)

       def __rshift__[B](
           self,
           other: Monad["Validated[Any]", B],
       ) -> "Validated[B]":
           return self.then(other)

       def __eq__(self, other: object) -> bool:
           if not isinstance(other, Validated):
               return False
           if self.is_valid() and other.is_valid():
               return self._value == other._value
           return self._errors == other._errors

       def __repr__(self) -> str:
           if self.is_valid():
               return f"Valid({self._value!r})"
           return f"Invalid({self._errors!r})"

Using the finished type
------------------------

All operators and do-notation work without any extra implementation:

.. code-block:: python

   from katharos.syntax_sugar import Do

   def validate_name(name: str) -> Validated[str]:
       name = name.strip()
       if not name:
           return Validated.Invalid("name cannot be blank")
       return Validated.Valid(name)

   def validate_age(age: int) -> Validated[int]:
       if age < 0 or age > 150:
           return Validated.Invalid(f"age {age} is out of range")
       return Validated.Valid(age)

   # Chaining with |
   result = (
       validate_name("Alice")
       | (lambda name: validate_age(30).fmap(lambda age: {"name": name, "age": age}))
   )
   print(result)  # Valid({'name': 'Alice', 'age': 30})

   # Do-notation
   with Do[Validated]() as do:
       name   = do.arrow(validate_name("Alice"))
       age    = do.arrow(validate_age(30))
       record = do.ret(lambda name, age: {"name": name, "age": age}, name=name, age=age)

   print(record)  # Valid({'name': 'Alice', 'age': 30})

   # Short-circuit on invalid
   with Do[Validated]() as do:
       name   = do.arrow(validate_name(""))       # Invalid — block short-circuits here
       age    = do.arrow(validate_age(30))
       record = do.ret(lambda name, age: {"name": name, "age": age}, name=name, age=age)

   print(record)  # Invalid(['name cannot be blank'])
