Katharos Documentation
======================

**Katharos** is a functional programming library for Python that provides algebraic abstractions like Semigroups, Monoids, Functors, Applicatives, and Monads, along with immutable data structures to enable composable, type-safe, and side-effect-free code.

.. image:: ../logo.png
   :alt: Katharos Logo
   :width: 200px
   :align: center

Installation
------------

Install Katharos using pip or uv:

.. code-block:: bash

   # Using pip
   pip install katharos

   # Using uv
   uv add katharos

Quick Examples
---------------

**Monoids: Combining Values**

.. code-block:: python

   from katharos.types.monoid import Sum, Product

   # Monoids provide identity elements and combine operations
   # Sum: additive monoid with identity 0
   total = Sum[int].identity()  # 0
   total = total @ Sum[int](5)  # 5
   total = total @ Sum[int](3)  # 8
   print(total)  # Sum(8)

   # Product: multiplicative monoid with identity 1
   result = Product[int].identity()  # 1
   result = result @ Product[int](4)  # 4
   result = result @ Product[int](3)  # 12
   print(result)  # Product(12)

**Functors: Safe Data Transformations**

.. code-block:: python

   from katharos.types import Maybe

   # Safe optional value handling with fmap
   result = Maybe.Just(5).fmap(lambda x: x * 2)
   print(result)  # Just(10)

   # Automatic short-circuiting on Nothing
   nothing = Maybe.Nothing().fmap(lambda x: x * 2)
   print(nothing)  # Nothing()

   # Chain transformations
   pipeline = (
       Maybe.Just(10)
       .fmap(lambda x: x * 2)      # 20
       .fmap(lambda x: x + 5)      # 25
   )
   print(pipeline)  # Just(25)

**Monads: Chaining Operations**

.. code-block:: python

   from katharos.types import Result

   def safe_divide(a: float, b: float) -> Result[Exception, float]:
       if b == 0:
           return Result.Failure(ZeroDivisionError("Division by zero"))
       return Result.Success(a / b)

   # Chain monadic operations with bind (|)
   result = (
       safe_divide(100, 4)
       | (lambda x: safe_divide(x, 2))  # 25 / 2 = 12.5
   )
   print(result)  # Success(12.5)

   # Error propagation
   error = (
       safe_divide(100, 0)
       | (lambda x: safe_divide(x, 2))
   )
   print(error)  # Failure(ZeroDivisionError('Division by zero'))

**Do Syntax: Readable Monadic Code**

.. code-block:: python

   from katharos.syntax_sugar import do, DoBlock
   from katharos.types import Maybe

   def get_value(x: int) -> Maybe[int]:
       return Maybe.Just(x) if x > 0 else Maybe.Nothing()

   # Clean, imperative-style monadic code
   @do(Maybe)
   def do_block() -> DoBlock[int]:
       x: int = yield get_value(5)
       y: int = yield get_value(3)
       return x + y

   print(do_block())  # Just(8)

Documentation Structure
-----------------------

This documentation follows the `Diátaxis framework <https://diataxis.fr/>`_, organizing content into four distinct categories:

📚 **Tutorials** - :doc:`tutorials/index`
   Learning-oriented lessons that take you through a series of steps to get you familiar with the concepts.
   Start here if you're new to `katharos`.

🔧 **How-To Guides** - :doc:`how-to/index`
   Problem-oriented guides that help you solve specific tasks.
   Use these when you know what you want to accomplish.

📖 **Reference** - :doc:`reference/index`
   Information-oriented technical descriptions of the API.
   Look here for detailed information about classes, functions, and modules.

💡 **Explanation** - :doc:`explanation/index`
   Understanding-oriented discussions that clarify and illuminate topics.
   Read these to deepen your understanding of concepts.

.. toctree::
   :maxdepth: 1
   :hidden:
   :caption: Tutorials

   tutorials/index

.. toctree::
   :maxdepth: 1
   :hidden:
   :caption: How-To Guides

   how-to/index

.. toctree::
   :maxdepth: 1
   :hidden:
   :caption: Reference

   reference/index

.. toctree::
   :maxdepth: 1
   :hidden:
   :caption: Explanation

   explanation/index

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
