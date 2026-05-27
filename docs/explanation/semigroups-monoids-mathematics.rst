The Mathematics of Semigroups and Monoids
==========================================

Functors, applicatives, and monads are about *contexts* — wrapping a
value in a structure that does something on top of it. Semigroups and
monoids are about something more elementary: *combining*. When do two
things of the same kind have a natural way to be combined into a third
thing of that same kind? When can you safely add up a long list of
them? When can the list be empty? These three questions are exactly
what the semigroup and monoid abstractions answer.

Despite their plain-sounding names, semigroups and monoids are the
quiet workhorses of functional programming. They are the foundation
under list concatenation, numeric summation, string joining,
``Map.merge``, ``reduce``, ``map-reduce``, parallel folds, optional
combination, and a dozen other operations that are everywhere but
rarely named. Naming them — and pinning down their laws — is what
turns these scattered patterns into a single uniform vocabulary.

This explanation is independent of :doc:`functors-mathematics`,
:doc:`applicatives-mathematics`, and :doc:`monads-mathematics`.
Semigroups and monoids form a separate algebraic hierarchy in
Katharos — they live in their own module and have nothing structural
to do with ``fmap`` or ``bind``.

What Does It Mean to Combine?
------------------------------

Take two strings. There is an obvious way to combine them: concatenate
them. ``"foo" + "bar" == "foobar"``. Take two integers. There are two
obvious ways: add them, or multiply them. Take two lists. Concatenate
them. Take two sets. Take their union, or their intersection. Take two
dictionaries. Merge them.

In every case, you have a *binary operation* — a function that takes
two values of some type ``S`` and returns a value of the same type
``S``. The operation does not change types; whatever ``S`` is going
in, ``S`` is coming out. This closure under the operation is the first
requirement.

But not every binary operation deserves to be called a combination.
Consider subtraction. ``(10 - 5) - 3 == 2``, but ``10 - (5 - 3) == 8``.
The way you group the operands changes the answer. Subtraction is a
binary operation on integers, but it is a brittle one — if someone
hands you a list ``[10, 5, 3]`` and asks you to "combine them with
``-``," there is no single right answer.

The structures we are about to define exist precisely to rule that
brittleness out.

Semigroup: The Associative Operation
-------------------------------------

A **semigroup** is a type ``S`` equipped with a binary operation
``op : S × S → S`` that satisfies one law:

**Associativity.** Grouping does not matter::

   (a op b) op c == a op (b op c)

That is the entire definition. A type with a closed, associative
binary operation is a semigroup. In Katharos, ``op`` is exposed as the
``@`` operator::

   from katharos.types import NonEmptyList

   xs = NonEmptyList(["foo", "bar"])
   ys = NonEmptyList(["baz"])
   xs @ ys     # NonEmptyList(["foo", "bar", "baz"])

   # Associativity:
   a, b, c = NonEmptyList([1]), NonEmptyList([2]), NonEmptyList([3])
   (a @ b) @ c == a @ (b @ c)   # True

Associativity sounds modest. It is not. Associativity is what makes a
list of values *summable in any order of grouping*. It is what lets
``reduce`` produce the same answer whether it folds left-to-right or
right-to-left. It is what lets a parallel implementation split the
work across cores, combine pairs in any order, and join the partial
results without worrying about who finished first. Without
associativity, none of those optimisations are safe.

The non-example helps cement this. Subtraction is closed on integers,
but ``(a - b) - c != a - (b - c)`` in general. So ``int`` under
subtraction is *not* a semigroup. You cannot hand ``[10, 5, 3]`` to a
parallel reducer with ``-`` and expect a well-defined answer.

What Associativity Buys You
----------------------------

Associativity by itself is enough to do something powerful:
**fold a non-empty list**. Given values ``[x_1, x_2, ..., x_n]`` with
an associative ``op``, the expression::

   x_1 op x_2 op x_3 op ... op x_n

has the same value no matter how you parenthesise it. Katharos
captures this with ``F.sigma``, which combines all elements of a
``NonEmptyList`` of semigroups::

   from katharos.functools import F
   from katharos.types import NonEmptyList

   F.sigma(NonEmptyList([
       NonEmptyList([1, 2]),
       NonEmptyList([3]),
       NonEmptyList([4, 5]),
   ]))
   # NonEmptyList([1, 2, 3, 4, 5])

Notice the type constraint: ``F.sigma`` only accepts a
``NonEmptyList``. That is not arbitrary — it is the boundary at which
the semigroup interface runs out. With a semigroup alone, there is no
way to fold an empty list. There is no "neutral starting value" to
return. Semigroups can combine, but they cannot start from nothing.

To remove that restriction, we need one more piece of structure.

Monoid: Adding an Identity
---------------------------

A **monoid** is a semigroup ``M`` equipped with one extra thing: an
**identity element** ``e ∈ M`` satisfying two laws:

**Left identity.** Combining identity on the left does nothing::

   e op a == a

**Right identity.** Combining identity on the right does nothing::

   a op e == a

A monoid is, in plain terms, a semigroup with a "do-nothing element."
For integer addition, the identity is ``0`` (since ``0 + a == a + 0 == a``).
For multiplication, it is ``1``. For string concatenation, the empty
string ``""``. For list concatenation, the empty list ``[]``. For set
union, the empty set. For dictionary merge, the empty dictionary.

The pattern is unmistakable once you see it: the identity is always
"the empty version of the thing." That is not coincidence — it is
exactly what an identity element *means* in this context.

In Katharos, a monoid declares its identity through a classmethod::

   from katharos.types import Sum, ImmutableList

   Sum[int].identity()                  # Sum(0)
   ImmutableList[int].identity()        # ImmutableList([])

What the Identity Buys You
---------------------------

The identity unlocks the operation a semigroup could not perform: a
**fold over a possibly-empty collection**. Given any monoid ``M`` and
any list ``[x_1, ..., x_n]`` of ``M`` values (possibly empty), the
expression::

   e op x_1 op x_2 op ... op x_n

is always well-defined. If the list is empty, the answer is ``e``. If
it has one element, the answer is that element (by the identity law).
If it has many, associativity says it does not matter how they are
combined.

This is why ``sum([])`` returns ``0`` and ``"".join([])`` returns
``""``. Those are not special cases hacked in for the empty-list
edge — they are the identity element doing its job. A monoid is what
makes such a "default for empty" mathematically well-grounded.

Concrete Instances
-------------------

**Integers under addition (Sum).** ``op`` is ``+``, identity is ``0``::

   from katharos.types import Sum

   Sum(3) @ Sum(4)             # Sum(7)
   Sum(3) @ Sum[int].identity()  # Sum(3)

**Integers under multiplication (Product).** ``op`` is ``*``, identity
is ``1``::

   from katharos.types import Product

   Product(3) @ Product(4)       # Product(12)
   Product(7) @ Product[int].identity()  # Product(7)

The same set ``int`` carries two different monoid structures.
``Sum`` and ``Product`` are wrappers that pick which one you mean.
This is a common pattern: an underlying type may support several
plausible "combine" operations, and the monoid wrappers let you name
which structure you are using without ambiguity.

**ImmutableList under concatenation.** ``op`` is concatenation,
identity is the empty list::

   from katharos.types import ImmutableList

   xs = ImmutableList([1, 2])
   ys = ImmutableList([3, 4])
   xs @ ys                                    # ImmutableList([1, 2, 3, 4])
   xs @ ImmutableList[int].identity()         # ImmutableList([1, 2])

**NonEmptyList under concatenation.** ``op`` is concatenation. There
is no identity — the empty list is not a valid ``NonEmptyList``, so
the type *cannot* have one. ``NonEmptyList`` is therefore a semigroup
but not a monoid. This is mathematically honest: forcing an identity
where none exists would be lying about the structure of the type.

**MonoidMaybe.** A clever construction: ``MonoidMaybe[A]`` lifts any
semigroup ``A`` into a monoid by adding ``Nothing()`` as the identity::

   from katharos.types import MonoidMaybe, Maybe, Sum

   a = MonoidMaybe(Maybe.Just(Sum(3)))
   b = MonoidMaybe(Maybe.Just(Sum(4)))
   nothing = MonoidMaybe[Sum].identity()    # MonoidMaybe(Nothing)

   a @ b                                     # MonoidMaybe(Just(Sum(7)))
   a @ nothing                               # MonoidMaybe(Just(Sum(3)))
   nothing @ b                               # MonoidMaybe(Just(Sum(4)))

``MonoidMaybe`` is itself a small theorem about algebraic structure:
*every semigroup can be promoted to a monoid by adding an extra
"absent" element that acts as the identity*. The promotion is
mechanical. The construction is so canonical that ``MonoidMaybe``
gets to exist as a named type.

The Laws in Action
-------------------

The laws are not abstract slogans. Verify them on real Katharos
values.

**Associativity for Sum**::

   from katharos.types import Sum

   a, b, c = Sum(2), Sum(3), Sum(4)
   (a @ b) @ c == a @ (b @ c)      # True (both are Sum(9))

**Identity for Sum**::

   Sum(5) @ Sum[int].identity()      # Sum(5)  ✓
   Sum[int].identity() @ Sum(5)      # Sum(5)  ✓

**Associativity for ImmutableList**::

   from katharos.types import ImmutableList

   a = ImmutableList([1])
   b = ImmutableList([2])
   c = ImmutableList([3])
   (a @ b) @ c == a @ (b @ c)        # True (both are [1, 2, 3])

**Identity for ImmutableList**::

   xs = ImmutableList([1, 2, 3])
   xs @ ImmutableList[int].identity()    # ImmutableList([1, 2, 3])  ✓

The associative grouping and the do-nothing identity are real
properties of these types, not just notation. ``F.sigma`` and any
future fold helper can rely on them.

Why the Laws Matter
--------------------

Associativity and the identity laws are what turn a plain binary
operation into something you can build on.

**Reordering and refactoring.** Associativity means you can regroup a
chain of ``@`` operations however is most convenient without changing
the result. A long combination can be split into helpers; a tree of
small combinations can be flattened into a fold; partial sums can be
combined in any order. The math guarantees the result is the same::

   # For any lawful semigroup, these are equivalent:
   (a @ b) @ (c @ d)
   ((a @ b) @ c) @ d
   a @ (b @ c @ d)
   F.sigma(NonEmptyList([a, b, c, d]))

**Parallel reduction.** Associativity is the single property that lets
a sequential fold be parallelised. Split a long list across n workers,
each worker reduces its chunk, then a final pass combines the n
partial results. The answer is identical to a sequential reduce.
``map-reduce``, parallel ``fold`` in databases, GPU reductions —
they all assume associativity, because without it, every other
optimisation is unsafe.

**Folds over empty inputs.** The identity laws are what let you fold
an arbitrary collection — including an empty one — and get a defined
answer. ``sum([])`` is ``0``, ``"".join([])`` is ``""``, the empty
union is the empty set. None of these are special cases; they are
each just the identity of the relevant monoid. Code that depends on
this property is implicitly relying on the monoid laws.

**Honest abstraction.** Because the laws say precisely what a
semigroup and a monoid *are*, any type satisfying them supports the
same reasoning. You can write a generic ``combine_all`` that takes a
``NonEmptyList[Semigroup]`` and folds it, or a generic
``combine_with_default`` that takes any ``Iterable[Monoid]``, and the
function will work for ``Sum``, ``Product``, ``ImmutableList``,
``MonoidMaybe``, or any user-defined monoid — without knowing
anything about the concrete type beyond the contract.

Why Two Abstract Classes?
--------------------------

Python is duck-typed; any type could just expose ``op`` and
``identity`` methods directly. Why does Katharos split them into
``Semigroup`` and ``Monoid``?

The split mirrors the mathematical reality. Some types — like
``NonEmptyList`` — genuinely have an associative combine operation but
genuinely have no identity element. Collapsing the hierarchy into a
single class would force every implementer to either invent a fake
identity (lying about the structure) or refuse to participate (losing
the abstraction). The two-level hierarchy lets each type declare
exactly as much structure as it has, no more and no less.

The hierarchy also lets generic code state its requirements
precisely. ``F.sigma`` requires only ``Semigroup`` — it works on
``NonEmptyList`` precisely because it does not need an identity. A
generic fold over a possibly-empty collection would require
``Monoid``. The compiler (and the reader) can see at a glance which
operations a function relies on.

The honest caveat applies as always: Python cannot prove that an
``op`` implementation is associative, or that an ``identity`` actually
acts as a unit. The laws live in docstrings, tests, and the
implementer's discipline. The abstraction provides shared vocabulary
and a place to hang the rules; it does not enforce them.

The Classes in Katharos
------------------------

The two classes read as direct statements of the structure::

   class Semigroup[S](ABC):
       @abstractmethod
       def op(self, other: S) -> S:
           ...

       def __matmul__(self, other: S) -> S:
           return self.op(other)


   class Monoid[M](Semigroup[M]):
       @classmethod
       @abstractmethod
       def identity(cls) -> M:
           ...

``Monoid`` extends ``Semigroup`` — every monoid is automatically a
semigroup, exactly as the mathematics says. ``op`` is the binary
operation; ``identity`` is the classmethod that produces the unit
element. The ``@`` operator (defined via ``__matmul__``) is sugar for
``op``.

What the classes cannot enforce are the laws. Concrete types must
honour associativity (for ``Semigroup``) and the additional left/right
identity laws (for ``Monoid``). ``Sum``, ``Product``, ``ImmutableList``,
``NonEmptyList`` (semigroup only), and ``MonoidMaybe`` all do.

A Brief Note on the Wider Mathematics
--------------------------------------

Semigroups and monoids are the first two steps on a longer algebraic
staircase. Add an inverse element to a monoid and you have a **group**.
Add commutativity (``a op b == b op a``) and you have an **abelian
group**. Add a second compatible operation and you get **rings**,
**fields**, and the rest of abstract algebra. The patterns extend all
the way up to modern category-theoretic constructions.

Katharos stops at monoid because monoid is the level that captures
"combinable" in a way that is broad enough to be useful and narrow
enough to have meaningful laws. The richer structures matter in
specialised contexts (cryptography needs groups; numeric computation
needs rings), but for everyday combining, semigroup and monoid are
exactly the right level of abstraction.

Further Reading
---------------

- :doc:`functors-mathematics` — the parallel hierarchy on the context
  side of Katharos's algebra
- :doc:`../reference/type-hierarchy` — see how the ``Semigroup`` /
  ``Monoid`` track sits beside the ``Functor`` / ``Applicative`` /
  ``Monad`` track
- :doc:`../reference/operators` — the operator table, including ``@``
- :doc:`why-fp-in-python` — why these abstractions are worth bringing
  to Python at all
