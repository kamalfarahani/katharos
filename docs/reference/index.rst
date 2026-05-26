API Reference
=============

Complete technical reference for all Katharos modules, classes, and functions.

**Reference material is information-oriented.** It describes the machinery and how to operate it. This is where you look up specific details about the API.

Modules
-------

.. toctree::
   :maxdepth: 2

   api/algebra
   api/types
   api/functools
   api/syntax_sugar

Additional Reference
--------------------

.. toctree::
   :maxdepth: 1

   type-hierarchy
   operators

Quick Links
-----------

Core Abstractions
~~~~~~~~~~~~~~~~~

- :class:`katharos.algebra.Semigroup`
- :class:`katharos.algebra.Monoid`
- :class:`katharos.algebra.Functor`
- :class:`katharos.algebra.Applicative`
- :class:`katharos.algebra.Monad`

Data Types
~~~~~~~~~~

- :class:`katharos.types.Maybe`
- :class:`katharos.types.Result`
- :class:`katharos.types.ImmutableList`
- :class:`katharos.types.NonEmptyList`
- :class:`katharos.types.IO`

Utilities
~~~~~~~~~

- :class:`katharos.functools.F`
- :class:`katharos.syntax_sugar.do`
