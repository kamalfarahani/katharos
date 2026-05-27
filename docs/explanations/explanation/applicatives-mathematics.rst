The Mathematics of Applicatives
================================

A ``Functor`` lets you apply a one-argument function to a value sitting
inside a context — a ``Maybe``, an ``ImmutableList``, a ``Result``, an
``IO``. As soon as you try to apply a *two*-argument function to two
such values, ``fmap`` is not enough. The function and at least one
argument live outside the context; the values live inside it; ``fmap``
has no way to bring them together.

The **applicative functor** is the abstraction that fills that gap. It
extends ``Functor`` with just enough machinery — a way to inject a plain
value into the context (``pure``), and a way to apply a wrapped function
to a wrapped value (``ap``) — to lift functions of *any* arity into the
context, uniformly.

This explanation builds on :doc:`functors-mathematics`. If category
theory, morphisms, and the functor laws are unfamiliar, read that first.

Why Functors Are Not Enough
----------------------------

Consider a simple problem. You have two ``Maybe[int]`` values, and a
plain function ``add(x, y) = x + y``. You want the sum if both values
are ``Just``, and ``Nothing`` if either is missing.

With only ``fmap``, the best you can do is partially apply::

   from katharos.types import Maybe

   def add(x: int) -> Callable[[int], int]:
       return lambda y: x + y

   x = Maybe[int].Just(3)
   y = Maybe[int].Just(4)

   partial = x.fmap(add)
   # partial : Maybe[Callable[[int], int]]
   # — a function-of-int trapped inside a Maybe

Now you are stuck. You have ``partial : Maybe[int → int]`` and
``y : Maybe[int]``, and no way to apply the one to the other. ``fmap``
takes a *plain* function and a wrapped value; it has no operation that
takes a *wrapped* function and a wrapped value.

This is not a Maybe-specific problem. The same wall appears with
``ImmutableList`` (you want to combine all elements of one list with
all elements of another), with ``Result`` (you want to combine two
fallible computations), with ``IO`` (you want to combine two effectful
reads). In every case, ``fmap`` runs out of road at the second
argument.

The applicative interface is precisely what lets you take that next
step.

The Applicative Interface
--------------------------

An **applicative functor** is a functor ``F`` equipped with two
additional operations:

1. ``pure : A → F[A]`` — lift a plain value into the context.
2. ``<*> : F[A → B] → F[A] → F[B]`` — apply a wrapped function to a
   wrapped value.

In Katharos, ``pure`` is a classmethod and ``<*>`` is exposed as the
``**`` operator (with ``ap`` as the named method)::

   from katharos.types import Maybe

   Maybe.pure(3)                 # Just(3)
   Maybe[int].Just(3) ** Maybe[int].Just(add).fmap(...)
   # — the ** operator is applicative apply

The signature is the same as Haskell's ``<*>``, just inverted because
``ap`` is a method on the value side: ``value.ap(wrapped_func)`` is
``wrapped_func <*> value`` in Haskell notation.

With ``pure`` and ``ap``, the stuck example becomes unstuck::

   x = Maybe[int].Just(3)
   y = Maybe[int].Just(4)

   # add is curried: int → (int → int)
   wrapped_add = x.fmap(add)        # Just(add(3)) — a function inside Maybe
   result = y.ap(wrapped_add)       # Just(7)

Or with the operator::

   result = y ** x.fmap(add)        # Just(7)

If either ``x`` or ``y`` is ``Nothing``, the result is ``Nothing``. The
function's own value (``add`` itself) is also threaded through ``pure``
and ``ap`` if needed, allowing the same pattern to scale to three, four,
or any number of arguments. That uniformity is the whole point.

The Four Applicative Laws
--------------------------

Where a functor obeys two laws, an applicative obeys four. They are
more intricate than the functor laws, but each says something
straightforward in plain words. Below, ``id`` and ``compose`` are the
identity and composition functions, and ``**`` is applicative apply.

**Identity.** Applying the wrapped identity function changes nothing::

   v ** App.pure(id) == v

If you put the identity function into the context and apply it to ``v``,
you get ``v`` back. ``pure`` and ``ap`` cannot conspire to alter the
value when the function does nothing.

**Homomorphism.** ``pure`` is a faithful messenger::

   App.pure(x) ** App.pure(f) == App.pure(f(x))

Lifting ``x`` and ``f`` separately and then combining them inside the
context is the same as applying ``f`` to ``x`` outside the context and
lifting the result. ``pure`` does not add behaviour of its own — it
just injects.

**Interchange.** It does not matter which side is lifted by ``pure``
when applying a wrapped function to a plain value::

   App.pure(y) ** u == u ** App.pure(lambda f: f(y))

If ``u`` is a wrapped function and ``y`` is a plain value, you can
either lift ``y`` and apply ``u`` to it, or lift the action "feed
``y`` to me" and apply that to ``u``. Same answer.

**Composition.** Wrapped functions compose the way unwrapped ones do::

   w ** (v ** (u ** App.pure(compose))) == (w ** v) ** u

This is the applicative analogue of the functor composition law. It
guarantees that combining three wrapped pieces — two functions and a
value — gives the same result whether you compose the functions first
inside the context, or apply them one at a time.

These four laws together pin down what an applicative *is*. They look
finicky, but they encode a single underlying claim: ``pure`` and ``ap``
extend the functor structure in the only way that respects ordinary
function application.

An Intuition: Wrapped Function Application
-------------------------------------------

Where a functor is a sealed container that lets you act on its contents
without opening it, an applicative is the same container — but now you
can *also* combine multiple containers, provided you have a function
inside one of them.

Think of ``pure`` as "putting a single item into an empty box of this
type." Think of ``ap`` as "if the left box has values and the right
box has functions, apply functions to values according to the box's
rules." For ``Maybe``, those rules are short-circuiting (missing on
either side gives missing). For ``ImmutableList``, the rules are
cartesian (each function in one list applied to each value in the
other). The mechanism is the same; the box's notion of "combine"
differs.

A crucial property: in an applicative, the *structure* of the result
is determined by the structures of the inputs, not by their *values*.
With ``Maybe``, you can decide in advance whether the result will be
``Just`` or ``Nothing`` just by looking at the shapes of the
operands. With ``ImmutableList``, you can predict the length of the
result list from the lengths of the inputs without inspecting any
element. This independence is exactly what separates an applicative
from a monad, where the structure of a later step *can* depend on the
value produced by an earlier one. We will come back to this.

Concrete Instances
-------------------

**Maybe as an applicative.** ``pure(x)`` is ``Just(x)``. ``ap``
short-circuits: if either operand is ``Nothing``, the result is
``Nothing``; otherwise the wrapped function is applied to the wrapped
value::

   from katharos.types import Maybe

   def add(x: int) -> Callable[[int], int]:
       return lambda y: x + y

   x = Maybe[int].Just(3)
   y = Maybe[int].Just(4)

   y ** x.fmap(add)                              # Just(7)
   y ** Maybe[int].Nothing().fmap(add)           # Nothing()
   Maybe[int].Nothing() ** x.fmap(add)           # Nothing()

**ImmutableList as an applicative.** ``pure(x)`` is a singleton
``ImmutableList([x])``. ``ap`` takes the cartesian product: every
function in the wrapped-functions list is applied to every value in
the wrapped-values list::

   from katharos.types import ImmutableList

   values = ImmutableList([1, 2, 3])
   funcs = ImmutableList([
       lambda x: x + 10,
       lambda x: x * 100,
   ])

   values.ap(funcs)
   # ImmutableList([11, 12, 13, 100, 200, 300])

The result has length ``len(funcs) * len(values)``. The list's notion
of "combine two contexts" is "every pairing," and ``ap`` realises it.

**Result and IO.** ``Result`` mirrors ``Maybe`` with an error channel:
the first ``Failure`` propagates. ``IO`` defers everything — ``pure``
wraps a value as a trivial action, ``ap`` builds a compound action
whose ``.execute()`` runs both sub-actions and applies one's result to
the other's. Same four laws, four different concrete behaviours.

The Laws in Action
-------------------

Take ``Maybe`` and check two of the laws by hand.

**Identity** says ``v ** App.pure(id) == v``::

   from katharos.types import Maybe
   from katharos.functools import F

   v = Maybe[int].Just(5)
   v ** Maybe.pure(F.id)             # Just(5)   ✓

   n = Maybe[int].Nothing()
   n ** Maybe.pure(F.id)             # Nothing() ✓

For ``Just(5)``: the wrapped identity is applied to ``5``, yielding
``5``. For ``Nothing()``: ``ap`` short-circuits without calling
anything. Both leave ``v`` unchanged.

**Homomorphism** says ``App.pure(x) ** App.pure(f) == App.pure(f(x))``::

   def double(x: int) -> int: return x * 2

   left  = Maybe.pure(3) ** Maybe.pure(double)   # Just(6)
   right = Maybe.pure(double(3))                 # Just(6)
   # left == right  ✓

Lifting ``3`` and ``double`` separately and combining them inside
``Maybe`` matches lifting ``double(3)`` directly. ``pure`` adds no
behaviour beyond injection.

The same laws hold for ``ImmutableList``, ``Result``, and ``IO``. The
concrete computations look different — the cartesian product on lists
is visibly different from short-circuiting on ``Maybe`` — but the
equations themselves are identical.

Why the Laws Matter
--------------------

The applicative laws, like the functor laws, are not bureaucracy. They
encode a precise contract that has practical consequences.

**Refactoring with confidence.** The composition law guarantees that
you can regroup applicative expressions without changing their
meaning. A pipeline that applies three wrapped functions in succession
is equivalent to one that composes them first and applies the result.
The math frees you from worrying about parenthesisation.

**Independence of structure and value.** The four laws together mean
the *shape* of an applicative result depends only on the *shapes* of
its inputs. This is why a function lifted into ``Maybe`` cannot decide
to be ``Just`` based on the wrapped values, and why a function lifted
into ``ImmutableList`` cannot decide to return fewer or more results
than the cartesian product implies. The structure is fixed up front.

**Parallel and independent evaluation.** Because applicative steps
cannot depend on each other's *values*, only on their *shapes*, they
can in principle be evaluated in parallel, in any order, or even
speculatively. This is the central reason applicative-style code is
preferred over monadic-style code when no dependency exists between
steps: it is strictly more amenable to optimisation.

**The boundary with Monad.** A monad lets a later step inspect the
value produced by an earlier step. An applicative does not. This
sounds like a limitation, and in expressive power it is — but it is
also a *guarantee*. An applicative computation cannot branch on its
own intermediate results, which makes it easier to reason about, to
analyse statically, and (where possible) to parallelise. Choosing
applicative over monad when both work is a deliberate trade of
expressiveness for predictability.

Why an Abstract Class at All?
------------------------------

The same question that applies to ``Functor`` applies here: Python is
duck-typed, so each concrete type could just expose its own ``pure``
and ``ap`` methods and skip the abstract base. Why does Katharos ship
an ``Applicative`` ABC?

For the same reasons — the ABC is where the four laws are stated, and
it is the link in the hierarchy that ``Monad`` extends. Without the
explicit declaration, "is this type an applicative?" has no meaningful
answer, and the upward composition (``Monad`` requires ``Applicative``
which requires ``Functor``) collapses.

The same honest trade-off applies, too: Python cannot prove that an
``ap`` implementation satisfies identity, homomorphism, interchange,
and composition. The laws live in the docstring, the tests, and the
implementer's discipline. The abstraction gives you a shared
vocabulary and a place to hang the rules; it does not enforce them.

The ``Applicative`` Class in Katharos
--------------------------------------

With this background, the ``Applicative`` base class reads as a direct
statement of the interface::

   class Applicative[App, A](Functor[App, A], ABC):

       @classmethod
       @abstractmethod
       def pure[T](cls, x: T) -> Applicative[App, T]:
           ...

       @abstractmethod
       def ap[B](
           self,
           wrapped_funcs: Applicative[App, Callable[[A], B]],
       ) -> Applicative[App, B]:
           ...

Notice that ``Applicative`` extends ``Functor``: every applicative is
automatically a functor. The ``pure`` classmethod is the value-lifting
operation; ``ap`` is the wrapped-function-application operation. The
``**`` operator (defined via ``__pow__``) is sugar for ``ap``.

The type parameter ``A`` is the value inside the context. ``App`` is
the applicative itself (``Maybe``, ``ImmutableList``, etc.). The ``B``
in ``ap`` is the type the wrapped function returns — so ``ap`` takes
an ``Applicative[App, A → B]`` and produces an ``Applicative[App, B]``,
exactly as the type ``<*> : F[A → B] → F[A] → F[B]`` requires.

What the class cannot enforce, as before, are the four laws. They are
the responsibility of each concrete type. ``Maybe``, ``ImmutableList``,
``Result``, ``NonEmptyList``, and ``IO`` all honour them.

Further Reading
---------------

- :doc:`functors-mathematics` — the prequel, on the abstraction
  ``Applicative`` extends
- :doc:`../reference/type-hierarchy` — see where ``Applicative`` sits
  between ``Functor`` and ``Monad``
- :doc:`../reference/operators` — the operator table, including ``**``
- :doc:`../tutorials/monadic-computation` — see how ``Applicative``
  fits alongside ``Monad`` in practical pipelines
