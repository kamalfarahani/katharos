Types Module
============

.. automodule:: katharos.types
   :no-members:

Maybe
-----

.. autoclass:: katharos.types.Maybe
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__, __or__, __pow__, __eq__, __repr__, __hash__

MonoidMaybe
-----------

.. autoclass:: katharos.types.MonoidMaybe
   :members:
   :undoc-members:
   :show-inheritance:

Result
------

.. autoclass:: katharos.types.Result
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__, __or__, __pow__, __eq__, __repr__, __hash__

Either
------

``Either[L, R]`` holds a Left payload or a Right payload of unrestricted type.
``fmap``, ``bind`` and ``ap`` operate on Right values; Left values short-circuit.
``map_left`` and ``bimap`` transform branch payloads, while ``either`` returns
the result of the active branch's handler. Exceptions from callbacks propagate.

Construction uses ``Either.Left(value)`` or ``Either.Right(value)``. Both accept
``None`` as a payload. ``pure`` and ``ret`` create Right values. Direct
``Either(...)`` construction raises ``TypeError``.

For ``value.ap(wrapped_function)`` and ``value ** wrapped_function``, the
receiver's Left takes precedence if both operands are Left, matching
:class:`~katharos.types.Result`. Haskell's ``<*>`` gives the function operand
precedence instead.

.. autoclass:: katharos.types.Either
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__, __or__, __pow__, __rshift__, __eq__, __repr__, __hash__, __bool__

ImmutableList
-------------

.. autoclass:: katharos.types.ImmutableList
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__, __add__, __eq__, __repr__, __hash__, __len__, __getitem__, __contains__, __iter__

NonEmptyList
------------

.. autoclass:: katharos.types.NonEmptyList
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__, __matmul__

Lazy
----

.. autoclass:: katharos.types.Lazy
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__, __or__, __pow__, __rshift__, __repr__

IO
--

.. autoclass:: katharos.types.IO
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__, __or__

UnwrapError
-----------

.. autoclass:: katharos.types.UnwrapError
   :members:
   :show-inheritance:
