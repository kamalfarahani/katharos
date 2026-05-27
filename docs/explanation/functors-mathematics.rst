The Mathematics of Functors
============================

When you call ``fmap`` in Katharos, you are doing something that has a
precise mathematical meaning. The ``Functor`` class is not a convention
or a design pattern — it is a direct translation of a concept from
*category theory* called a *functor*. Understanding where functors
come from clarifies why the API looks the way it does, why the laws
are stated the way they are, and why the same ``fmap`` can work on
``Maybe``, ``ImmutableList``, ``Result``, and ``IO`` without any of
them being related by inheritance.

This explanation assumes the vocabulary of
:doc:`category-theory-primer` — categories, objects, morphisms,
identity, composition, and the "Py" category of Python types. If those
words are unfamiliar, read that primer first.

Functors: Mappings That Preserve Structure
-------------------------------------------

A **functor** is a mapping from one category to another that *preserves
structure*. Formally, a functor ``T : C → D`` between categories
``C`` and ``D`` consists of:

1. A mapping on objects: every object ``A`` in ``C`` maps to an object
   ``T(A)`` in ``D``.
2. A mapping on morphisms: every morphism ``f : A → B`` in ``C`` maps
   to a morphism ``T(f) : T(A) → T(B)`` in ``D``.

And it must satisfy two **functor laws**:

**Identity law**: The functor must preserve identity morphisms::

   T(id_A) = id_T(A)

Mapping the identity on ``A`` must give the identity on ``T(A)``. The
functor cannot introduce or remove identity behaviour.

**Composition law**: The functor must preserve composition::

   T(g ∘ f) = T(g) ∘ T(f)

Mapping a composed morphism must give the same result as mapping each
morphism separately and then composing the results. The functor cannot
change how morphisms chain together.

These two laws together mean that a functor is a *structure-preserving*
mapping — it translates one category into another without distorting the
relationships between objects and morphisms.

A useful intuition: a functor is a sealed container that lets you act on
whatever is inside without ever opening it. You hand it a function ``f``,
and the contents are transformed by ``f``, but the container itself —
its shape, its layout, its presence-or-absence — is left intact. The
laws are what guarantee the seal: ``fmap`` cannot reach in and rearrange
the structure, only transform the values within it.

Endofunctors: Functors From Py to Py
-----------------------------------------

A functor where the source and target are the *same* category is called
an **endofunctor**.

The functors in Katharos are endofunctors on Py — they map Python types
and functions *back into* Python types and functions. Here is how:

**Maybe as an endofunctor**

The object mapping takes every Python type ``A`` and maps it to
``Maybe[A]``:

.. code-block:: text

   int     →  Maybe[int]
   str     →  Maybe[str]
   float   →  Maybe[float]

The morphism mapping is ``fmap``. Given any function ``f : A → B``,
``fmap(f)`` produces a function ``Maybe[A] → Maybe[B]``::

   from katharos.types import Maybe

   # f : int → str
   f = str

   # fmap lifts f to: Maybe[int] → Maybe[str]
   Maybe[int].Just(42).fmap(f)    # Just('42')
   Maybe[int].Nothing().fmap(f)   # Nothing()

The lifted function applies ``f`` to the wrapped value if one exists, and
propagates ``Nothing()`` otherwise.

**ImmutableList as an endofunctor**

The object mapping takes every type ``A`` to ``ImmutableList[A]``:

.. code-block:: text

   int     →  ImmutableList[int]
   str     →  ImmutableList[str]

The morphism mapping is again ``fmap``. Given ``f : A → B``, ``fmap(f)``
produces a function ``ImmutableList[A] → ImmutableList[B]``::

   from katharos.types import ImmutableList

   lengths = ImmutableList(["cat", "elephant", "ox"])
   result = lengths.fmap(len)   # ImmutableList([3, 8, 2])

Here ``fmap`` applies ``f`` to every element in the list.

These are the same mathematical operation — lifting a function into a
computational context — expressed by two completely different concrete
behaviours.

The Laws in Action
-------------------

The laws are not just theoretical. They show up directly in the behaviour
of Katharos values. Take ``Maybe`` and check both laws against it.

**Identity law.** Applying the identity function under ``fmap`` must
return a value indistinguishable from the original::

   from katharos.types import Maybe
   from katharos.functools import F

   Maybe[int].Just(5).fmap(F.id)      # Just(5)   ✓
   Maybe[int].Nothing().fmap(F.id)    # Nothing() ✓

The ``Just`` case applies ``F.id`` to ``5``, producing ``5``, so you get
``Just(5)`` back. The ``Nothing`` case never calls the function at all,
so ``Nothing()`` passes through unchanged. In both cases, ``x.fmap(F.id)``
equals ``x``.

**Composition law.** Applying two functions in sequence via two
``fmap`` calls must equal applying their composition in a single
``fmap``::

   def increment(x: int) -> int: return x + 1
   def double(x: int) -> int:    return x * 2

   value = Maybe[int].Just(3)

   two_steps = value.fmap(increment).fmap(double)
   # Just(3) → Just(4) → Just(8)

   one_step = value.fmap(F.compose(double)(increment))
   # Just(3) → Just(8)

   # two_steps == one_step == Just(8)  ✓

For ``Nothing()``, both sides produce ``Nothing()`` regardless of the
functions — the composition law holds vacuously there.

The same two laws hold for ``ImmutableList``, where the preserved
structure is the sequence of elements rather than presence-or-absence::

   from katharos.types import ImmutableList

   xs = ImmutableList([1, 2, 3])
   xs.fmap(F.id)                                  # ImmutableList([1, 2, 3])  ✓
   xs.fmap(increment).fmap(double)                # ImmutableList([4, 8, 12])
   xs.fmap(F.compose(double)(increment))          # ImmutableList([4, 8, 12]) ✓

And for ``Result``, where ``Failure`` propagates the way ``Nothing``
does, and for ``IO``, where ``fmap`` schedules the transformation to run
when ``.execute()`` is eventually called. Different concrete behaviours,
the same two equations.

Why the Laws Matter
--------------------

The functor laws are not arbitrary bureaucracy. They encode a precise
guarantee: a lawful functor is a *transparent container*. It affects
only the *structure* (presence or absence for Maybe, sequence of elements
for ImmutableList), never the *values themselves*.

This has several practical consequences:

**Refactoring with confidence.** The composition law means you can always
merge consecutive ``fmap`` calls into one, or split one into many, without
changing the result. If you want to inline a transformation or factor out
a pipeline step, the math guarantees the result is the same::

   # These are always equivalent for any lawful functor:
   x.fmap(f).fmap(g)
   x.fmap(F.compose(g)(f))

**Predictable semantics.** The identity law means ``fmap`` can never
invent data or discard data from the container's structure. A ``Just``
remains a ``Just``; a ``Nothing`` remains a ``Nothing``; a list of three
elements remains a list of three elements.

**A shared interface across unrelated types.** Because the laws say
precisely what a functor *is*, any type satisfying them supports the same
reasoning. You do not need to know whether you are dealing with ``Maybe``,
``Result``, ``ImmutableList``, or ``IO`` to know that chaining two
``fmap`` calls is safe and equivalent to one composed ``fmap``. The
abstraction is honest because the laws are real constraints.

**A foundation for further abstraction.** Applicatives and monads
(represented in Katharos by ``Applicative`` and ``Monad``) are built on
top of functors. Every monad is an applicative; every applicative is a
functor. The functor laws are the ground floor that the richer structures
stand on.

The ``Functor`` Class in Katharos
-----------------------------------

With this background, the ``Functor`` base class reads as a direct
statement of the endofunctor structure::

   class Functor[F, A](ABC):
       @abstractmethod
       def fmap[B](self, f: Callable[[A], B]) -> Functor[F, B]:
           ...

The type parameter ``A`` is the object in Py. ``fmap`` takes a
morphism ``f : A → B`` and produces a value of type ``Functor[F, B]`` —
this is the morphism mapping. The type variable ``F`` names the functor
itself (``Maybe``, ``ImmutableList``, etc.).

What the class *cannot* enforce is the laws. Nothing in Python's type
system prevents a broken ``fmap`` implementation that violates identity
or composition. The docstring states them, the mathematics demands them,
but it is the responsibility of each concrete implementation to honour
them. Both ``Maybe`` and ``ImmutableList`` do.

Further Reading
---------------

- :doc:`category-theory-primer` — the prerequisite vocabulary used here
- :doc:`applicatives-mathematics` — extends ``Functor`` with the
  ability to apply n-ary functions
- :doc:`monads-mathematics` — extends ``Applicative`` with sequential
  dependency between steps
- :doc:`../tutorials/functor` — use ``fmap`` hands-on in a data pipeline
- :doc:`../reference/type-hierarchy` — see where ``Functor`` sits in the
  full algebraic hierarchy
