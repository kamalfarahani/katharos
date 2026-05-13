Katharos Documentation
======================

**Katharos** is a functional programming library for Python that provides algebraic abstractions like Semigroups, Monoids, Functors, Applicatives, and Monads, along with immutable data structures to enable composable, type-safe, and side-effect-free code.

.. image:: ../logo.png
   :alt: Katharos Logo
   :width: 200px
   :align: center

Installation
------------

Install Katharos using pip:

.. code-block:: bash

   pip install katharos

Quick Example
-------------

.. code-block:: python

   from katharos.types import Maybe

   # Safe optional value handling
   result = Maybe.Just(5).fmap(lambda x: x * 2)
   print(result)  # Just(10)

   # Automatic short-circuiting on Nothing
   nothing = Maybe.Nothing().fmap(lambda x: x * 2)
   print(nothing)  # Nothing()

Documentation Structure
-----------------------

This documentation follows the `Diátaxis framework <https://diataxis.fr/>`_, organizing content into four distinct categories:

📚 **Tutorials** - :doc:`tutorials/index`
   Learning-oriented lessons that take you through a series of steps to complete a project.
   Start here if you're new to Katharos or functional programming.

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
   :maxdepth: 2
   :hidden:
   :caption: Tutorials

   tutorials/index
   tutorials/getting-started
   tutorials/first-monad
   tutorials/functor-pipeline
   tutorials/error-handling
   tutorials/immutable-lists

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: How-To Guides

   how-to/index
   how-to/chain-operations
   how-to/do-notation
   how-to/custom-semigroups
   how-to/error-handling
   how-to/function-composition
   how-to/side-effects

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Reference

   reference/index
   reference/api/algebra
   reference/api/types
   reference/api/functools
   reference/api/syntax_sugar
   reference/type-hierarchy
   reference/operators

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Explanation

   explanation/index
   explanation/fp-concepts
   explanation/algebraic-abstractions
   explanation/monoids-semigroups
   explanation/monad-laws
   explanation/immutability
   explanation/comparison

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
