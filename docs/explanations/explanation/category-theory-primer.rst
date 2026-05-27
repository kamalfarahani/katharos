Just Enough Category Theory to Understand Katharos
====================================================

Several of Katharos's abstractions — ``Functor``, ``Applicative``,
``Monad`` — are direct translations of concepts from *category theory*,
a branch of mathematics concerned with structure and the relationships
between structures. The class names, the method names, and especially
the laws are not invented; they have precise mathematical meanings
that pre-date any programming language.

You do not need to know category theory to *use* Katharos. But knowing
the bare minimum — what a category is, what makes Python's types form
one — makes the rest of the algebra hierarchy stop looking arbitrary
and start looking like a coherent translation. That is the goal of
this short primer.

This primer is the only place where category-theoretic vocabulary is
built up from scratch. The downstream explanation docs
(:doc:`functors-mathematics`, :doc:`applicatives-mathematics`,
:doc:`monads-mathematics`) all assume what is established here. Read
this once and the others can be read in any order.

Categories: Structure Without Detail
--------------------------------------

Category theory is sometimes called "the mathematics of mathematics."
Rather than studying numbers, or sets, or shapes directly, it studies
the *structure* that all of those things share.

A **category** has three components:

**Objects** — the things in the category. In a category of sets, the
objects are sets. In a category of logical propositions, the objects are
propositions.

**Morphisms** (also called arrows) — relationships between objects. Each
morphism has a *source* object and a *target* object. If ``f`` is a
morphism from ``A`` to ``B``, we write ``f : A → B``.

**Composition** — a rule for combining morphisms. If ``f : A → B`` and
``g : B → C``, then there must exist a combined morphism ``g ∘ f : A → C``
(read "g after f"). Composition must be *associative*: for any three
composable morphisms, it does not matter in which order you group the
composition steps.

Additionally, every object must have an **identity morphism** — a
morphism ``id_A : A → A`` that, when composed with any other morphism,
leaves it unchanged:

.. code-block:: text

   id_B ∘ f = f       (composing identity on the left does nothing)
   f ∘ id_A = f       (composing identity on the right does nothing)

That's the complete definition. No numbers, no sets, no specific content
— just objects, arrows between them, a way to chain arrows, and identity
arrows.

The Category of Python Types
------------------------------

Now here is the key move: Python types and functions form a category.

**Objects** are Python types: ``int``, ``str``, ``bool``, ``float``,
your own dataclasses, etc.

**Morphisms** are Python functions. A function ``f`` with signature
``Callable[[A], B]`` is a morphism from type ``A`` to type ``B``::

   def double(x: int) -> int: ...        # morphism int → int
   def to_str(x: int) -> str: ...        # morphism int → str
   def is_even(x: int) -> bool: ...      # morphism int → bool

**Composition** is function composition. In Katharos, ``F.compose``
implements this. Given ``f : A → B`` and ``g : B → C``::

   from katharos.functools import F

   def increment(x: int) -> int:
       return x + 1

   def double(x: int) -> int:
       return x * 2

   double_then_increment = F.compose(increment)(double)
   # F.compose(g)(f) produces g ∘ f — apply f first, then g
   # double_then_increment(3) == 7

**Identity morphisms** are the identity function. ``F.id`` returns
its argument unchanged::

   F.id(42)     # 42
   F.id("hello") # "hello"

You can verify the category laws hold. Composition is associative:
``h ∘ (g ∘ f)`` and ``(h ∘ g) ∘ f`` always produce the same function.
Identity does nothing: ``F.compose(F.id)(f) == f`` for any ``f``.

This category — Python types and functions between them — is called
**Py**.

A caveat in passing: this treats Python functions as total, pure, and
terminating. Real Python functions can raise, loop forever, mutate state,
or return ``None`` on inputs they're not supposed to receive. Py is an
idealisation, and the algebraic laws hold to the extent your code
respects it. Haskell makes exactly the same compromise with its
category "Hask" — the math is genuinely useful even when the underlying
language is messier than the model.

Where to Go From Here
----------------------

With "Py" in hand — the category of Python types and functions — you
can read the rest of the Katharos algebra hierarchy as direct
translations of category-theoretic concepts:

- :doc:`functors-mathematics` — the next step: mappings *between*
  categories that preserve structure, and the abstraction the
  ``Functor`` class captures.
- :doc:`applicatives-mathematics` — extends ``Functor`` with the
  ability to apply n-ary functions to wrapped values.
- :doc:`monads-mathematics` — extends ``Applicative`` with sequential
  dependency: each step can decide the next based on what it found.

None of those documents introduce additional category theory beyond
what is here. They use this vocabulary to describe specific structures
that ride on top of Py.
