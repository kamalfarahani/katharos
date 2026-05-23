How to Compose and Curry Functions
====================================

This guide shows you how to use ``F.compose``, ``F.curry``, ``F.foldl``, and ``F.foldr`` to build reusable function pipelines without writing boilerplate wrapper functions.

Prerequisites
-------------

- ``katharos`` installed
- Functions you want to combine into a pipeline

Composing two functions with ``F.compose``
---------------------------------------

``F.compose(f)(g)`` returns a new function that applies ``g`` first and then ``f`` — equivalent to ``f(g(x))``:

.. code-block:: python

   from katharos.functools import F

   strip   = str.strip
   upper   = str.upper
   exclaim = lambda s: s + "!"

   shout = F.compose(exclaim)(F.compose(upper)(strip))

   print(shout("  hello world  "))  # 'HELLO WORLD!'

Because each ``F.compose(f)`` returns a single-argument function, you can chain calls to build longer pipelines left-to-right:

.. code-block:: python

   pipeline = F.compose(exclaim)(
                  F.compose(upper)(
                      strip
                  )
              )

For pipelines with many steps, use ``F.foldl`` over a list of transforms (see below).

Currying a multi-argument function
------------------------------------

``F.curry`` converts a function that takes multiple arguments into a chain of single-argument functions. Pass arguments one at a time to produce specialised partial functions:

.. code-block:: python

   def clamp(lo: float, hi: float, x: float) -> float:
       return max(lo, min(hi, x))

   curried_clamp = F.curry(clamp)

   clamp_0_100 = curried_clamp(0.0)(100.0)   # fix lo and hi
   print(clamp_0_100(150.0))   # 100.0
   print(clamp_0_100(-5.0))    #   0.0
   print(clamp_0_100(42.0))    #  42.0

Keyword arguments are also supported:

.. code-block:: python

   clamp_grade = curried_clamp(lo=0.0)(hi=10.0)
   print(clamp_grade(11.5))  # 10.0

Building a reusable transform list with ``F.foldl``
----------------------------------------------

``F.foldl(f, acc, xs)`` applies ``f(acc, element)`` left-to-right over ``xs``. Use it to apply a sequence of transforms to an initial value:

.. code-block:: python

   transforms = [
       str.strip,
       str.lower,
       lambda s: s.replace(" ", "_"),
   ]

   slug = F.foldl(lambda acc, f: f(acc), "  Hello World  ", transforms)
   print(slug)  # 'hello_world'

Folding from the right with ``F.foldr``
-----------------------------------

``F.foldr(f, acc, xs)`` processes ``xs`` right-to-left, passing each element and the accumulated value to ``f(element, acc)``. Use it when the combining function is right-associative — for example building a string right-to-left:

.. code-block:: python

   words  = ["cat", "sat", "mat"]
   joined = F.foldr(lambda word, acc: word + (", " + acc if acc else ""), "", words)
   print(joined)  # 'cat, sat, mat'

Combining compose and curry for point-free pipelines
------------------------------------------------------

Curry a multi-argument function first, then compose the partial applications:

.. code-block:: python

   def add(a: float, b: float) -> float:
       return a + b

   def multiply(a: float, b: float) -> float:
       return a * b

   add5      = F.curry(add)(5)
   double    = F.curry(multiply)(2)
   add5_then_double = F.compose(double)(add5)

   print(add5_then_double(10))  # (10 + 5) * 2 == 30

Using ``F.id`` as a neutral element
---------------------------------

``F.id`` returns its argument unchanged. Use it as a starting accumulator when folding a list of transforms:

.. code-block:: python

   pipeline = F.foldl(
       lambda acc, f: F.compose(f)(acc),
       F.id,
       [str.strip, str.upper, lambda s: "[" + s + "]"],
   )

   print(pipeline("  notice  "))  # '[NOTICE]'
