Concurrency Module
==================

.. automodule:: katharos.concurrency
   :no-members:

Threading Backends
------------------

BaseThreadingBackend
~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: katharos.concurrency.BaseThreadingBackend
   :members:
   :undoc-members:
   :show-inheritance:

ThreadingBackend
~~~~~~~~~~~~~~~~~

.. autoclass:: katharos.concurrency.ThreadingBackend
   :members:
   :undoc-members:
   :show-inheritance:

default_backend
~~~~~~~~~~~~~~~

.. autofunction:: katharos.concurrency.default_backend

Thread Handles
--------------

BaseThreadHandle
~~~~~~~~~~~~~~~~~

.. autoclass:: katharos.concurrency.BaseThreadHandle
   :members:
   :undoc-members:
   :show-inheritance:

ThreadingHandle
~~~~~~~~~~~~~~~~

.. autoclass:: katharos.concurrency.ThreadingHandle
   :members:
   :undoc-members:
   :show-inheritance:

Synchronization Protocols
-------------------------

AbstractLock
~~~~~~~~~~~~

.. autoclass:: katharos.concurrency.AbstractLock
   :members:
   :undoc-members:
   :show-inheritance:

AbstractCondition
~~~~~~~~~~~~~~~~~

.. autoclass:: katharos.concurrency.AbstractCondition
   :members:
   :undoc-members:
   :show-inheritance:

CSP Primitives
==============

.. automodule:: katharos.concurrency.csp
   :no-members:

CSPRuntime
----------

.. autoclass:: katharos.concurrency.csp.CSPRuntime
   :members:
   :undoc-members:
   :show-inheritance:

.. autodata:: katharos.concurrency.csp.csp

Channel
-------

``send(value)`` returns ``Result[ChannelClosedError, None]``: ``Success(None)``
when a buffered channel accepts the value or an unbuffered receiver takes it,
and ``Failure(ChannelClosedError("send on closed channel"))`` when closure
prevents completion. Blocked senders wake on closure. A completed unbuffered
hand-off remains successful even when closure precedes the sender resuming.

.. warning::

   Breaking change: ``send`` previously returned ``None`` and raised
   ``ChannelClosedError`` on closure. Callers that caught that exception must
   now inspect the returned ``Result`` with ``is_failure()`` and ``error``.
   ``close()`` still raises ``ChannelClosedError`` if already closed.

.. autoclass:: katharos.concurrency.csp.Channel
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__, __iter__, __repr__

Go
--

.. autoclass:: katharos.concurrency.csp.Go
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__, __call__, __enter__, __exit__

select
------

.. autofunction:: katharos.concurrency.csp.select

.. autofunction:: katharos.concurrency.csp.recv

SelectResult
~~~~~~~~~~~~

.. autoclass:: katharos.concurrency.csp.SelectResult
   :show-inheritance:
   :exclude-members: index, channel, value, is_default, is_timeout
   :special-members: __repr__

Exceptions
----------

.. autoexception:: katharos.concurrency.csp.ChannelClosedError
   :show-inheritance:

.. autoexception:: katharos.concurrency.csp.ChannelTimeoutError
   :show-inheritance:
