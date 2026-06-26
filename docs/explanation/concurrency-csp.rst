Communicating Sequential Processes: Design and Rationale
========================================================

Katharos coordinates concurrent work by *passing messages*, not by sharing memory
and guarding it with locks. Its first concurrency model is CSP — Communicating
Sequential Processes — built from three primitives: channels carry values between
threads, goroutines run work concurrently, and ``select`` chooses among several
channels. This article explains why the module is shaped the way it is: why the
backend is swappable, why channels behave as they do, why goroutines are deliberately
forgetful, and how ``select`` manages to wait on many channels at once.

CSP is the first model under a broader *message-passing* umbrella for the library.
Other models (actors, for example) are planned to live alongside it. The unifying idea
is the one Go popularized: *don't communicate by sharing memory; share memory by
communicating.* Instead of several threads reaching into the same mutable state and
racing for a lock, each piece of work owns its own state and hands values to others
through a channel. The channel becomes the single point of synchronization, which is
far easier to reason about than locks scattered across the code.

A swappable concurrency backend
-------------------------------

A CSP library has to spawn threads and use synchronization primitives, but it does not
have to be married to one particular threading library. Katharos pushes all of that
behind a :class:`~katharos.concurrency.BaseThreadingBackend`: an abstraction with just
four operations — spawn a callable, create a lock, create a condition variable, and
create context-local storage. :class:`~katharos.concurrency.ThreadingBackend`, built on
the standard library, is the default.

The payoff is that the *concurrency model* is decoupled from the *execution substrate*.
Channels and goroutines are written once against the abstraction; swapping in a
green-thread backend (greenlet or gevent, say) changes how work is scheduled without
touching a line of the CSP code. The ``AbstractLock`` and ``AbstractCondition``
protocols are intentionally minimal — only the context-manager and wait/notify surface
that the channels actually use — so a standard ``threading.Lock`` satisfies them
structurally, and so does a green-thread equivalent.

This is also why a :class:`~katharos.concurrency.csp.CSPRuntime` *requires* an explicit
backend rather than reaching for a hidden global. An earlier design exposed a
module-level launcher; it was deliberately removed. A global singleton quietly couples
every channel and goroutine in a program to one backend chosen somewhere out of sight,
which is exactly the implicit shared state CSP sets out to avoid. Making the backend an
explicit argument keeps the choice visible and local: the default ``csp`` runtime is
there for convenience, but you can always construct a runtime bound to a backend you
control.

Channels: rendezvous versus buffering
-------------------------------------

A channel's ``capacity`` is not just a performance knob; it changes the *meaning* of a
send. An **unbuffered** channel (the default) is a synchronous rendezvous: a ``send``
blocks until some other thread is ready to ``recv``, so the two sides meet at a single
moment and the hand-off doubles as synchronization. A **buffered** channel decouples
the two sides: a ``send`` only blocks once the buffer is full, letting a fast producer
run ahead of a slow consumer up to a bounded backlog. Choosing a capacity is really
choosing how tightly you want producer and consumer coupled.

Getting the unbuffered hand-off *correct* under contention is subtler than it looks.
The naive approach — a sender concludes its value was received once the buffer looks
empty again — breaks when several senders compete: another sender refilling the buffer
is indistinguishable from your value being taken. Katharos avoids this by giving each
in-flight value its own slot object and having the sender wait on *that slot's*
identity. A receiver marks the specific slot it took as ``taken``; the sender wakes and
checks its own slot, never confusing its hand-off with someone else's. The correctness
comes from waiting on "my value was received," not on a shared, ambiguous condition.

Every channel operation wakes *all* waiters with ``notify_all`` rather than trying to
wake exactly the right one. This is a conscious trade of throughput for correctness:
waking all waiters is O(number of waiters), but it sidesteps a whole class of
lost-wakeup and wrong-waiter bugs that targeted ``notify`` invites. For a library that
values being obviously correct over being maximally fast, that is the right default; a
channel with thousands of simultaneously blocked peers would feel it, but that is a rare
shape.

Finally, ``recv`` does not return a bare value — it returns a
:class:`~katharos.types.Result`. "The channel is closed" and "the wait timed out" are
not exceptional events to be caught somewhere up the stack; they are ordinary outcomes
you will routinely branch on. Modeling them as ``Failure(ChannelClosedError)`` and
``Failure(ChannelTimeoutError)`` makes them visible in the type and impossible to ignore,
the same errors-as-values discipline the rest of the library uses (see
:doc:`error-handling-and-tracebacks`). Iterating a channel is the sugar on top: the loop
simply ends when ``recv`` reports closure.

Goroutines and structured concurrency
-------------------------------------

``csp.go(fn, ...)`` launches work concurrently and returns immediately, mirroring Go's
``go func()``. Like a goroutine, it is deliberately forgetful: the callable's return
value is discarded, and an exception it raises does not propagate back to the launcher.
That can be surprising, but it is the honest consequence of concurrency — the launching
thread has already moved on, so there is no call stack left for a return value or
exception to flow into. The CSP answer is consistent with everything else in the module:
if you want a result or a failure back, send it over a channel. Communication is the
channel's job, not the launcher's.

Fire-and-forget is fine for truly independent work, but most concurrent code wants to
*wait* for the work it started. Used as a ``with`` block, ``csp.go`` becomes a
structured-concurrency scope: every task launched inside is tracked, and leaving the
block blocks until all of them finish — even if the block exits because of an exception.
This is what stops concurrency from leaking. Without a scope, an error in the middle of
a function can leave threads running with no one waiting on them and no one to notice
they failed. With a scope, the lifetime of concurrent work is bounded by a block you can
see, and the indentation tells you exactly when it all completes. For the deeper argument
behind structured concurrency — and why an unscoped "go" is a footgun — see Nathaniel J.
Smith's `Notes on structured concurrency, or: Go statement considered harmful
<https://vorpus.org/blog/notes-on-structured-concurrency-or-go-statement-considered-harmful/>`_.

``select``: choosing between channels
-------------------------------------

Channels and goroutines are enough to move values around, but real programs need to wait
on *whichever* of several things happens first: a result or a timeout, work or a
cancellation signal, any of several producers. That is what ``select`` provides, and it
is the third pillar of CSP precisely because the first two cannot express it.

Implementing it is the hard part, because of a structural fact: every channel owns its
*own* condition variable. There is no shared lock you can wait on to be notified about
"any of these channels," and a standard condition can only wait on one thing at a time.
The obvious workaround — poll each channel in a loop with a small sleep — was rejected.
Polling burns CPU while idle and adds latency proportional to the poll interval, neither
of which is acceptable for a primitive meant to block efficiently.

Instead, ``select`` registers a small shared object — an auto-reset event — as an
*observer* on every channel in the call. Whenever a channel changes state (a value
arrives, or it closes), it signals its observers in addition to its own waiters. The
selector then follows a simple, robust loop: poll every channel once, and if none is
ready, block on the shared event until some channel signals it, then poll again.

Two properties make this correct rather than merely plausible. First, **the poll is
authoritative**: readiness is decided by actually looking in each channel's buffer, and
the signal only serves to *wake* the selector — never to tell it a value exists. A
signal that arrives at an awkward moment cannot cause a value to be missed, because the
next poll re-checks the real state; a stale signal that corresponds to a value already
taken by someone else simply leads to a poll that finds nothing and goes back to
waiting. The retained "signaled" flag closes the lost-wakeup window: a signal landing
between a poll and the wait is remembered, not lost. Second, the **lock ordering is
acyclic** — a channel, while holding its own lock, may signal the selector, but the
selector never grabs a channel lock while holding its own — so no amount of contention
can deadlock.

One visible behavior is worth calling out as a deliberate trade-off. When several
channels are ready at once, Katharos picks the first in argument order; Go randomizes.
Determinism makes ``select`` easier to test and reason about, at the cost of fairness:
a channel that is *continuously* ready can starve later cases. For the typical uses —
racing work against a timeout, draining several producers that are not all saturated —
this never bites, and the predictability is worth more than statistical fairness. If you
need fairness, you can order or rotate the cases yourself.

Putting it together: the runtime
--------------------------------

:class:`~katharos.concurrency.csp.CSPRuntime` is the small piece that ties everything to
one backend. It bundles a backend-bound channel class and a backend-bound goroutine
launcher, so channels you create and work you launch through the same runtime all run on
— and synchronize through — the same backend. The default ``csp`` instance is that
runtime bound to the default threading backend, which is why the tutorial and how-to can
write ``csp.Channel[int](...)`` and ``csp.go(...)`` without ever mentioning a backend.
Swapping the whole concurrency substrate is then a single, local change: construct a
``CSPRuntime`` with a different backend and build everything through it.

Further reading
---------------

- :doc:`../tutorials/csp` — learn the primitives hands-on by building a worker pool
- :doc:`../how-to/concurrency_csp` — task-focused recipes for channels, goroutines, and ``select``
- :doc:`../reference/api/concurrency` — full API for the CSP primitives and backends
- :doc:`error-handling-and-tracebacks` — the errors-as-values discipline behind ``recv``
  returning a ``Result``
