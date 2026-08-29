Building Reusable Functions with compose and curry
===================================================

In this tutorial, we will build a text processing pipeline using function composition and partial application. Along the way, we will encounter ``F.compose``, ``F.curry``, and ``F.foldl`` - and see how combining small functions produces flexible, reusable building blocks.

Prerequisites
-------------

- Python 3.13 or later
- Katharos installed (see :doc:`getting-started`)
- Complete the :doc:`functor` tutorial so you are familiar with transforming values with functions

Step 1: Compose Two Functions
------------------------------

Create a new file called ``transform.py`` with the following contents:

.. code-block:: python

   from katharos.functools import F

   shout = F.compose(lambda s: s + "!")(str.upper)

   print(shout("hello"))
   print(shout("world"))

Run the file:

.. code-block:: bash

   python transform.py

You should see:

.. code-block:: text

   HELLO!
   WORLD!

Notice the argument order: ``F.compose(f)(g)`` applies ``g`` first and then ``f``. Here ``str.upper`` runs first, then the exclamation mark is added.

Step 2: Compose Three Functions
---------------------------------

Now we will chain a third transformation. Add this code at the bottom of ``transform.py``:

.. code-block:: python

   strip_and_shout = F.compose(shout)(str.strip)

   print(strip_and_shout("  hello  "))

Run the file. The new line at the bottom should be:

.. code-block:: text

   HELLO!

Notice that composing an already-composed function works the same way: ``str.strip`` runs first, ``str.upper`` second, and the ``"!"`` is appended last.

Step 3: Curry a Multi-Argument Function
-----------------------------------------

Now we will curry a function so it can be applied one argument at a time. Add this code at the bottom of ``transform.py``:

.. code-block:: python

   def repeat(times: int, separator: str, text: str) -> str:
       return separator.join([text] * times)

   curried_repeat = F.curry(repeat)

   print(curried_repeat(3)("-")("ha"))

Run the file. The new line should be:

.. code-block:: text

   ha-ha-ha

Notice that ``curried_repeat(3)`` returned a new function that still expects ``separator`` and ``text``. Each call with one argument returns another function until all arguments are supplied.

.. note::

   ``F.curry`` does not preserve type hints. The curried function and all its partial applications have the type ``Callable``, not the specific signature of the original function. Your type checker will not flag incorrect argument types passed to a curried function. Annotate the original function carefully, since that is where type safety lives.

Step 4: Create Reusable Partial Functions
------------------------------------------

The real power of currying is creating specialised functions from a general one. Add this code at the bottom of ``transform.py``:

.. code-block:: python

   triple = curried_repeat(3)
   triple_dash = triple("-")
   triple_comma = triple(", ")

   print(triple_dash("knock"))
   print(triple_comma("ready"))

Run the file. The new lines should be:

.. code-block:: text

   knock-knock-knock
   ready, ready, ready

Notice that ``triple`` and ``triple_dash`` are reusable functions created for free from ``curried_repeat``. No new ``def`` statements were needed.

Step 5: Fold a List into a Single Value
-----------------------------------------

Now we will reduce a list to a single value using ``F.foldl``. Add this code at the bottom of ``transform.py``:

.. code-block:: python

   words = ["functional", "programming", "is", "fun"]
   sentence = F.foldl(lambda acc, word: acc + " " + word, words[0], words[1:])
   print(sentence)

Run the file. The new line should be:

.. code-block:: text

   functional programming is fun

Notice how ``foldl`` processes the list from left to right, accumulating the result. The second argument (``words[0]``) is the starting accumulator value.

Step 6: Build a Complete Text Processing Pipeline
--------------------------------------------------

Now we will combine everything into a pipeline that normalises a list of raw user inputs. Replace the bottom of ``transform.py`` (from the Step 5 code onwards) with:

.. code-block:: python

   raw_inputs = ["  hello world  ", "  PYTHON  ", " functional  "]

   normalise = F.compose(str.lower)(str.strip)

   cleaned = [normalise(s) for s in raw_inputs]
   print(cleaned)

   join_with_pipe = F.curry(lambda sep, items: sep.join(items))("|")
   result = join_with_pipe(cleaned)
   print(result)

Run the file. The new lines should be:

.. code-block:: text

   ['hello world', 'python', 'functional']
   hello world|python|functional

Notice how ``normalise`` is assembled from two small functions, and ``join_with_pipe`` is a reusable specialisation of a curried join function. Neither required its own ``def`` statement.

What We Built
-------------

We built a text processing pipeline that composes small functions into larger ones with ``F.compose``, creates reusable partial applications with ``F.curry``, and reduces a list to a single value with ``F.foldl``. Each building block remained a plain function that can be tested and reused independently.
