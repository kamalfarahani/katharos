The Mathematics of Monads
==========================

A ``Functor`` lets you apply a unary function inside a context. An
``Applicative`` lets you apply n-ary functions to several wrapped
values. But both share a quiet limitation: the *function* you apply
must be decided in advance. Neither ``fmap`` nor ``ap`` lets a later
step look at the value produced by an earlier step and choose what to
do next based on what it found.

The **monad** is the abstraction that closes that gap. It adds one
operation, ``bind``, that takes a wrapped value and a *function that
itself returns a wrapped value*. That tiny shift - letting the
continuation depend on the previous result - is what makes monadic
code expressive enough to model parsing, configuration lookup,
short-circuit error handling, list comprehensions, and effectful I/O,
all with the same three-law contract.

This explanation builds on :doc:`functors-mathematics` and
:doc:`applicatives-mathematics`. Read those first if the functor and
applicative laws are unfamiliar.

Why Applicatives Are Not Enough
--------------------------------

Suppose you are looking up a user, and then - only if the user exists
- looking up that user's manager. Both lookups return ``Maybe[User]``.

With ``ap`` alone, you cannot express this. ``ap`` requires both
operands to be ready before it runs. It can combine ``Maybe[User]``
and ``Maybe[User → Maybe[User]]``, but the manager-lookup function
needs the actual ``User`` value to know which manager to look up, and
``ap`` will not give it to you::

   from katharos.types import Maybe

   def find_user(name: str) -> Maybe[User]: ...
   def find_manager(user: User) -> Maybe[User]: ...

   user = find_user("alice")
   # user : Maybe[User]

   # You cannot write this with ap. The find_manager function needs
   # the User value to even start, but ap can only combine wrapped
   # values with wrapped functions - not chain one onto another.

The shape of the *second* computation depends on the *value* produced
by the first. Applicatives are deliberately not allowed that
dependency - that is exactly the property that lets them be evaluated
in parallel. To get sequential dependency back, you need a stronger
operation.

``bind`` is that operation.

The Monad Interface
--------------------

A **monad** is an applicative ``M`` equipped with two operations:

1. ``ret : A → M[A]`` - lift a plain value into the monad. (In
   Katharos, ``ret`` is an alias for ``pure`` inherited from
   ``Applicative``.)
2. ``bind : M[A] → (A → M[B]) → M[B]`` - feed the wrapped value to a
   function that produces a new wrapped value, and flatten the result.

In Katharos, ``bind`` is exposed as the ``|`` operator (Haskell's
``>>=``). The motivating example writes naturally::

   user_and_manager = find_user("alice") | find_manager
   # find_user("alice") : Maybe[User]
   # find_manager      : User → Maybe[User]
   # result            : Maybe[User]

If ``find_user`` returns ``Nothing()``, ``bind`` short-circuits and
``find_manager`` is never called. If it returns ``Just(alice)``,
``find_manager(alice)`` runs, and its ``Maybe[User]`` result is the
final value - *not* a ``Maybe[Maybe[User]]``. The "flatten" half of
``bind`` is what prevents the nesting from piling up.

The key thing to notice is that the type of ``f`` in ``m.bind(f)`` is
``A → M[B]``, not ``A → B``. The continuation is itself monadic. That
is what lets it decide its own *shape* - to return ``Nothing()`` and
end the chain, to return a list of any length, to schedule new
side-effects - based on the value it received.

The Three Monad Laws
---------------------

Where a functor obeys two laws and an applicative obeys four, a monad
obeys three. They are simpler than the applicative laws, and each says
something concrete about how ``ret`` and ``bind`` must fit together.

**Left identity.** ``ret`` is a transparent wrapper on the left::

   M.ret(a).bind(f) == f(a)

Lifting ``a`` into the monad and then binding ``f`` is the same as
just calling ``f(a)``. ``ret`` cannot add behaviour of its own.

**Right identity.** ``ret`` is a transparent wrapper on the right::

   m.bind(M.ret) == m

Binding ``ret`` over a monadic value is a no-op. ``ret`` cannot strip
behaviour either.

**Associativity.** It does not matter how you group a chain of binds::

   m.bind(f).bind(g) == m.bind(lambda x: f(x).bind(g))

You can bind ``f`` first and then ``g``, or you can fuse them into a
single continuation that binds ``g`` inside ``f``. The result is the
same.

These three laws together pin down a deeper claim: ``bind`` makes the
type ``A → M[B]`` into a kind of *composable arrow*. If you define
"Kleisli composition" as ``(f >=> g) = lambda x: f(x).bind(g)``, the
monad laws are exactly the statement that ``>=>`` is associative and
that ``ret`` is its identity. In other words, the monad laws say:
*monadic functions form a category, with ``ret`` as identity and
``>=>`` as composition.* The three laws are not arbitrary - they are
the standard category laws applied at one level of remove.

An Intuition: Each Step Decides the Next
-----------------------------------------

Where a functor is a sealed container and an applicative is a
container you can combine with other containers, a monad is a
container whose *unpacking* drives what happens next. Each ``bind``
step says: "open the box, and based on what you find, build the next
box."

This is the property that distinguishes monads from applicatives, and
it is worth dwelling on. In an applicative pipeline, all the steps and
their shapes are determined up front; only the values inside flow
through. In a monadic pipeline, the *shape itself* of the next step is
a function of what came before. ``find_manager`` decides whether to
return ``Just`` or ``Nothing`` based on the user it receives. A
list-bind step decides how many results to produce based on the
element it sees. An ``IO`` step can schedule different reads depending
on the result of an earlier read.

That power has a cost. Because a monadic step depends on previous
values, monadic computations are inherently sequential - you cannot
parallelise them the way applicatives allow. This is why "use
``Applicative`` when both work, ``Monad`` only when you need it" is a
genuine guideline, not a stylistic preference. The trade-off is
expressiveness against analysability.

Concrete Instances
-------------------

**Maybe as a monad.** ``ret(x)`` is ``Just(x)``. ``bind`` short-circuits
on ``Nothing``::

   from katharos.types import Maybe

   def safe_div(x: int) -> Callable[[int], Maybe[int]]:
       return lambda y: Maybe.Nothing() if y == 0 else Maybe.Just(x // y)

   Maybe.Just(10) | safe_div(10)         # Just(1)
   Maybe.Just(0)  | safe_div(10)         # Nothing()
   Maybe.Nothing() | safe_div(10)        # Nothing()

The chain stops at the first ``Nothing()``. The continuation after it
is never called.

**ImmutableList as a monad.** ``ret(x)`` is the singleton
``ImmutableList([x])``. ``bind`` is the classical *flatMap* or
*concatMap* - apply the function to each element, then concatenate::

   from katharos.types import ImmutableList

   xs = ImmutableList([1, 2, 3])
   xs | (lambda n: ImmutableList([n, n * 10]))
   # ImmutableList([1, 10, 2, 20, 3, 30])

Each step decides how many results to emit. List comprehensions are
secretly a monadic notation for exactly this operation.

**Result and IO.** ``Result`` mirrors ``Maybe`` with an error channel:
``bind`` short-circuits at the first ``Failure``, propagating the
exception. ``IO`` chains effectful steps: ``bind`` produces a new
deferred action whose ``.execute()`` runs the first action, feeds its
result to the continuation, and then runs whatever action the
continuation produced. Same three laws, four different concrete
behaviours.

The Laws in Action
-------------------

Take ``Maybe`` and check the laws by hand.

**Left identity**: ``M.ret(a).bind(f) == f(a)``::

   from katharos.types import Maybe

   def to_just_double(x: int) -> Maybe[int]:
       return Maybe.Just(x * 2)

   left  = Maybe.ret(5) | to_just_double     # Just(10)
   right = to_just_double(5)                 # Just(10)
   # left == right  ✓

Lifting ``5`` into ``Maybe`` and then binding ``to_just_double`` is
the same as just calling ``to_just_double(5)``.

**Right identity**: ``m.bind(M.ret) == m``::

   m = Maybe.Just(7)
   m | Maybe.ret                              # Just(7)  ✓

   n = Maybe.Nothing()
   n | Maybe.ret                              # Nothing() ✓

Binding ``Maybe.ret`` over either case returns the original. ``ret``
adds nothing on the right side either.

**Associativity**: ``m.bind(f).bind(g) == m.bind(lambda x: f(x).bind(g))``::

   def add_one(x: int) -> Maybe[int]:   return Maybe.Just(x + 1)
   def double(x: int)  -> Maybe[int]:   return Maybe.Just(x * 2)

   m = Maybe.Just(3)

   left  = (m | add_one) | double                          # Just(8)
   right = m | (lambda x: add_one(x) | double)             # Just(8)
   # left == right  ✓

You can bind step by step, or fuse the two continuations into one;
either grouping yields the same answer. For ``Nothing()``, both sides
short-circuit and produce ``Nothing()`` - associativity holds
vacuously there.

The same three laws hold for ``ImmutableList``, ``Result``, and
``IO``, with their respective concrete meanings.

Why the Laws Matter
--------------------

The monad laws are the contract that makes monadic code refactorable
and reasonable.

**Refactoring with confidence.** Associativity means you can regroup,
inline, or extract chains of binds freely. A long pipeline can be
broken into a helper without changing semantics; two helpers can be
fused into one. The math guarantees the result is the same::

   # These are always equivalent for any lawful monad:
   (m | f) | g
   m | (lambda x: f(x) | g)

**``ret`` is a true unit.** Left and right identity together say that
``ret`` is not a meaningful step in a computation. You can always
introduce or remove ``ret`` at the boundaries of a bind chain without
changing behaviour. This is what lets sugar like do-notation
*automatically* lift the final plain expression: the final ``return``
in a ``@do(Maybe)`` block is implicitly ``Maybe.ret(...)``, and the
laws guarantee that adding it changes nothing.

**Do-notation works at all.** Katharos's ``@do`` decorator translates a
generator-based syntax into a series of ``bind`` calls. The translation
is only sound because of associativity - successive ``yield`` statements
correspond to successive binds, and the laws guarantee that any way of
parenthesising the resulting bind tree gives the same answer. Without
the laws, the sugar would not be faithful to the semantics.

**Sequencing is meaningful.** ``then`` (the ``>>`` operator) is defined
as ``self.bind(lambda _: other)`` - discard the first result and run
the second. The monad laws ensure that ``>>`` is associative and that
``M.ret(x) >> m == m``, so ``>>`` behaves like the sequencing operator
you would expect from any imperative language.

**The boundary with Applicative - revisited.** Every monad gives you
an applicative for free: ``mf ** mx`` can be implemented as
``mf.bind(lambda f: mx.bind(lambda x: M.ret(f(x))))``. The reverse is
not true. The monad laws are strictly stronger than the applicative
laws, and they buy you the ability to inspect intermediate values at
the cost of giving up structural independence between steps. Choose
deliberately.

Why an Abstract Class at All?
------------------------------

The same answer that applied to ``Functor`` and ``Applicative``
applies here. Python is duck-typed; each type could just expose
``bind`` and ``ret`` and call it a day. But:

- The ABC is where the three laws are stated.
- It is the top of the algebraic hierarchy that ``Maybe``,
  ``ImmutableList``, ``Result``, ``NonEmptyList``, and ``IO`` all
  declare themselves part of. ``isinstance(x, Monad)`` is a meaningful
  question; "does ``x`` have a ``.bind`` method that behaves
  monadically" is not enforceable.
- Sugar like ``@do(Maybe)`` is parametric in the monad. The decorator
  takes any ``Monad`` subclass and produces correctly-translated
  do-notation - that uniformity is only possible because the
  ``Monad`` interface is declared, not merely conventional.

And the honest caveat repeats: Python cannot prove ``bind`` satisfies
left identity, right identity, and associativity. The laws live in
docstrings, tests, and discipline. The abstraction gives you shared
vocabulary and structural integration with the rest of the algebra; it
does not enforce correctness.

The ``Monad`` Class in Katharos
--------------------------------

With this background, the ``Monad`` base class reads as a direct
statement of the interface::

   class Monad[Mon, A](Applicative[Mon, A], ABC):

       @classmethod
       def ret[T](cls, x: T) -> Monad[Mon, T]:
           return cls.pure(x)

       @abstractmethod
       def bind[B](
           self,
           f: Callable[[A], Monad[Mon, B]],
       ) -> Monad[Mon, B]:
           ...

       def then[B](self, other: Monad[Mon, B]) -> Monad[Mon, B]:
           return self | (lambda _: other)

``Monad`` extends ``Applicative``, which extends ``Functor`` - every
monad is automatically an applicative and a functor. ``ret`` is a thin
alias over ``pure`` from ``Applicative``; ``bind`` is the new
operation; ``then`` is a derived sequencing helper defined in terms of
``bind``. The ``|`` operator is sugar for ``bind`` (via
``__or__``), and ``>>`` is sugar for ``then`` (via ``__rshift__``).

As always, what the class cannot enforce is the laws. Each concrete
type is responsible for honouring left identity, right identity, and
associativity. ``Maybe``, ``Result``, ``ImmutableList``,
``NonEmptyList``, and ``IO`` all do.

Further Reading
---------------

- :doc:`functors-mathematics` - the foundation of the algebraic
  hierarchy
- :doc:`applicatives-mathematics` - the middle layer, and the
  expressiveness/analysability trade-off with monads
- :doc:`../tutorials/monadic-computation` - using ``bind`` and ``then``
  in practical pipelines
- :doc:`../tutorials/do-syntax` - the generator-based sugar that the
  monad laws make sound
- :doc:`../reference/type-hierarchy` - where ``Monad`` sits in the
  full algebra
- :doc:`../reference/operators` - the operator table, including ``|``
  and ``>>``
