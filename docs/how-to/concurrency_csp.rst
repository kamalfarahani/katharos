How to Coordinate Concurrent Work with CSP
==========================================

This guide is a set of task-focused recipes for Katharos' CSP primitives:
launching concurrent work with ``csp.go``, passing values over a ``Channel``, and
choosing between operations with ``select``. Each section solves one concrete problem;
pick the one you need.

Prerequisites
-------------

- You know the basics of channels and goroutines. If not, work through the
  :doc:`../tutorials/csp` tutorial first.
- For the full signatures and options, see the :doc:`../reference/api/concurrency`
  reference.
- Every recipe uses the default runtime: ``from katharos.concurrency.csp import csp``
  (plus ``Channel``, ``recv``, ``select`` where noted). ``csp.go`` and
  ``csp.Channel`` supply the threading backend for you.

Run a function concurrently
---------------------------

Call ``csp.go`` with the function and its arguments. It starts the work on another
thread and returns immediately with a handle:

.. code-block:: python

   from katharos.concurrency.csp import csp

   def greet(name: str) -> None:
       print(f"hello, {name}")

   handle = csp.go(greet, "world")
   handle.join()   # hello, world

A launched callable is fire-and-forget: its return value is discarded and any
exception it raises does **not** propagate to the caller. To get results or failures
back, use a channel (see below).

Wait for spawned work to finish
-------------------------------

For a single task, keep the handle and call ``join``. For a *group* of tasks, use
``csp.go`` as a ``with`` block: the scope joins everything launched inside it before
the block exits, so you never track handles by hand.

.. code-block:: python

   import threading

   from katharos.concurrency.csp import csp

   lock = threading.Lock()
   done: list[int] = []

   def record(n: int) -> None:
       with lock:
           done.append(n)

   with csp.go:
       for n in range(3):
           csp.go(record, n)
   # the block has joined all three workers here
   print(sorted(done))   # [0, 1, 2]

Prefer the ``with`` block over collecting handles yourself. It turns ``csp.go`` into
a *structured-concurrency scope*, which gives you:

- **Automatic joining.** Every task launched inside the block is joined when the
  block exits, so you never have to keep a list of handles and join each one. Adding
  another ``csp.go(...)`` inside the block needs no extra bookkeeping.
- **Guaranteed cleanup on errors.** The scope joins its work *even if the block
  raises*, so a spawned task can never outlive the block. Without it, an exception in
  the middle of your code would leak still-running threads.
- **A bounded lifetime.** The indentation makes the lifetime of the concurrent work
  obvious at a glance: everything started inside finishes before the program moves
  past the block. Outside any ``with`` block, ``csp.go`` is pure fire-and-forget and
  is not tracked.
- **Correct nesting.** Scopes are tracked per execution context, so they nest: an
  inner ``with csp.go`` joins only its own work, and a shared ``csp`` runtime stays
  safe to use from several places at once.

For the deeper rationale behind scoping concurrent work this way (and why an
unscoped ``go`` is a footgun), see Nathaniel J. Smith's
`Notes on structured concurrency, or: Go statement considered harmful
<https://vorpus.org/blog/notes-on-structured-concurrency-or-go-statement-considered-harmful/>`_.

Get a result back from a goroutine
----------------------------------

Because a goroutine's return value is discarded, send the result over a channel and
receive it on the other side. An unbuffered channel makes this a synchronous hand-off:

.. code-block:: python

   from katharos.concurrency.csp import csp

   answer = csp.Channel[int]()

   def compute() -> None:
       answer.send(6 * 7)

   csp.go(compute)
   print(answer.recv().unwrap())   # 42

``recv`` returns a :class:`~katharos.types.Result`, so call ``unwrap`` to get the
value. To report a failure from the worker, send a ``Result.Failure`` (or a sentinel
value) instead of letting the exception vanish.

Decouple a fast producer from a slow consumer
---------------------------------------------

Give the channel a ``capacity`` so the producer can keep working while the consumer
catches up. A buffered ``send`` only blocks once the buffer is full:

.. code-block:: python

   from katharos.concurrency.csp import csp

   buffer = csp.Channel[int](capacity=3)

   buffer.send(1)
   buffer.send(2)
   buffer.send(3)   # all three succeed without a reader present
   print(buffer.recv().unwrap())   # 1

Stream a sequence and stop cleanly
----------------------------------

Have the producer ``close`` the channel when it is done. A closed channel is
iterable, so the consumer drains it with a plain ``for`` loop that ends automatically:

.. code-block:: python

   from katharos.concurrency.csp import csp

   stream = csp.Channel[int]()

   def produce() -> None:
       for n in range(3):
           stream.send(n)
       stream.close()

   csp.go(produce)

   for value in stream:
       print(value)        # 0, then 1, then 2

   # A recv after the channel is closed and drained reports the closure:
   print(stream.recv())    # Failure(ChannelClosedError('recv on closed channel'))

Fan work out to a pool and collect results
------------------------------------------

Run several workers against one shared ``jobs`` channel and gather their output from a
shared ``results`` channel. Close ``jobs`` to end the workers' loops, then use a
``with csp.go`` scope to wait for them before draining the results:

.. code-block:: python

   from katharos.concurrency.csp import csp

   jobs = csp.Channel[int](capacity=5)
   results = csp.Channel[int](capacity=5)

   def worker() -> None:
       for job in jobs:
           results.send(job * job)

   for n in range(1, 6):
       jobs.send(n)
   jobs.close()

   with csp.go:
       for _ in range(3):
           csp.go(worker)

   results.close()
   print(sorted(results))   # [1, 4, 9, 16, 25]

Results arrive in whatever order the workers finish, so sort (or otherwise aggregate)
them. See the :doc:`../tutorials/csp` tutorial for a step-by-step build of this pattern.

Wait on several channels at once
--------------------------------

Use ``select`` with one ``recv`` case per channel. It returns as soon as any case is
ready; when several are ready, the first in argument order wins. The result tells you
which case was chosen:

.. code-block:: python

   from katharos.concurrency.csp import csp, recv, select

   a = csp.Channel[str]()
   b = csp.Channel[str](capacity=1)
   b.send("from b")

   choice = select(recv(a), recv(b))
   print(choice.index)            # 1  (the b case)
   print(choice.value.unwrap())   # from b

Add a timeout
-------------

To bound a wait on a single channel, pass ``timeout`` to ``recv``; it returns a
``Failure(ChannelTimeoutError)`` if nothing arrives in time:

.. code-block:: python

   from katharos.concurrency.csp import csp

   idle = csp.Channel[int]()
   print(idle.recv(timeout=0.1))
   # Failure(ChannelTimeoutError('recv timed out after 0.1 seconds'))

To bound a wait across *several* channels, pass ``timeout`` to ``select`` and check
``is_timeout``:

.. code-block:: python

   from katharos.concurrency.csp import csp, recv, select

   a = csp.Channel[int]()
   b = csp.Channel[int]()

   choice = select(recv(a), recv(b), timeout=0.1)
   print(choice.is_timeout)   # True

Poll a channel without blocking
-------------------------------

Pass ``default=True`` to ``select`` to take a value if one is ready right now, or
return immediately otherwise. Check ``is_default`` to see whether nothing was ready:

.. code-block:: python

   from katharos.concurrency.csp import csp, recv, select

   ch = csp.Channel[int]()

   choice = select(recv(ch), default=True)
   print(choice.is_default)   # True  (nothing was waiting)

Signal cancellation to workers
------------------------------

Give a worker a dedicated ``done`` channel and have it ``select`` between real work and
the cancellation signal. Closing ``done`` makes its ``recv`` case ready, which stops
the worker. List the ``done`` case first so cancellation takes priority:

.. code-block:: python

   from katharos.concurrency.csp import csp, recv, select

   work = csp.Channel[int]()
   done = csp.Channel[int]()
   processed: list[int] = []

   def consumer() -> None:
       while True:
           choice = select(recv(done), recv(work))
           if choice.index == 0:        # done fired: stop
               return
           processed.append(choice.value.unwrap())

   handle = csp.go(consumer)

   work.send(1)
   work.send(2)
   done.close()                          # tell the consumer to stop
   handle.join()

   print(sorted(processed))   # [1, 2]

Handle closed and timed-out outcomes
------------------------------------

Both ``recv`` and a ``select`` case carry a ``Result``. Branch on it to react to each
outcome explicitly, distinguishing the two failure types by class:

.. code-block:: python

   from katharos.concurrency.csp import (
       ChannelClosedError,
       ChannelTimeoutError,
       csp,
   )

   ch = csp.Channel[int]()
   ch.close()

   outcome = ch.recv(timeout=0.1)
   if outcome.is_success():
       print("got", outcome.unwrap())
   elif isinstance(outcome.error, ChannelClosedError):
       print("channel closed")          # printed here
   elif isinstance(outcome.error, ChannelTimeoutError):
       print("timed out")

Pin or swap the threading backend
---------------------------------

The default ``csp`` runtime uses the standard-library threading backend. To pin a
specific backend (for example, to run a green-thread backend), build your own
``CSPRuntime`` and create channels and goroutines through it:

.. code-block:: python

   from katharos.concurrency import ThreadingBackend
   from katharos.concurrency.csp import CSPRuntime

   runtime = CSPRuntime(ThreadingBackend())
   ch = runtime.Channel[int](capacity=1)
   ch.send(99)
   print(ch.recv().unwrap())   # 99

To create a single channel against an explicit backend, pass ``backend=`` to
``Channel`` directly:

.. code-block:: python

   from katharos.concurrency import default_backend
   from katharos.concurrency.csp import Channel

   ch = Channel[int](capacity=1, backend=default_backend())
   ch.send(7)
   print(ch.recv().unwrap())   # 7

See also
--------

- :doc:`../tutorials/csp` — a guided, end-to-end build of a worker pool
- :doc:`../reference/api/concurrency` — full API for channels, goroutines, ``select``,
  and the backend abstractions
