Stress-test channels
====================

Use the repository's stress suite to investigate delivery errors, deadlocks,
closure races, timeout regressions, or leaked resources. Run these commands from
a Katharos checkout with Python 3.13 or later and ``uv`` installed.

Run the short suite
-------------------

Run the stress campaign and the harness's own fault checks:

.. code-block:: bash

   uv run pytest tests/concurrency/stress -v

The default ``ci`` campaign uses fixed seeds and runs 96 isolated cases across
standard conditions, non-reentrant conditions, and conditions with spurious
wake-ups. It covers capacities 0, 1, 2, and 16, and one-to-one, many-to-one,
one-to-many, and many-to-many communication. Every case has a 15-second watchdog.
The target is less than two minutes per Python version. The full test suite
includes this tier automatically, including the existing Python 3.13/3.14 CI jobs.

Run a longer campaign
---------------------

Choose a 15-minute stress run or a two-hour soak run:

.. code-block:: bash

   uv run python -m tests.concurrency.stress --profile stress --seed 3500
   uv run python -m tests.concurrency.stress --profile soak --seed 3500

The stress tier uses up to 32 producers and 32 consumers and a 30-second case
watchdog. The soak tier uses the same worker limit, longer message streams, and
a 60-second watchdog. Both tiers include capacity 256, rotate seeds between
rounds, and complete every scenario family at least once before checking the
campaign time budget. Consequently, a campaign may exceed its nominal duration
by the final case's runtime. Both stop on the first failure.

To select a single family or keep artifacts elsewhere:

.. code-block:: bash

   uv run python -m tests.concurrency.stress --profile stress --scenario select --seed 3500 --artifacts-dir /tmp/channel-select

The available families are ``delivery``, ``closure``, ``handoff``, ``timeouts``,
``select``, ``lifecycle``, ``model``, and ``history``. The long pytest equivalent is
``uv run pytest tests/concurrency/stress -m channel_stress --channel-stress=stress``.
Use ``--channel-stress-artifacts`` to set its output directory.

The manually dispatched **Channel stress campaign** GitHub Actions workflow
accepts a profile and seed, runs on Python 3.13 and 3.14, and uploads diagnostics.
Its job limit is three hours. Long runs do not run automatically on pushes.

Investigate a failure
---------------------

The default artifact directory is ``.stress-artifacts/``. Each failure retains:

* A JSON trace with the complete case configuration, Python version, last
  progress checkpoint, captured worker exceptions, and up to 4096 recent events.
* Standard output and standard error, including all-thread stack dumps when a
  case approaches its watchdog deadline.
* A failure summary with the exit status, watchdog outcome, and elapsed time.

``summary.json`` records campaign progress and failures; successful case traces
are removed. Copy the failure artifacts before rerunning into the same directory
if you need to preserve the campaign summary.

Replay the exact recorded workload configuration:

.. code-block:: bash

   uv run python -m tests.concurrency.stress --replay .stress-artifacts/FAILED-CASE.json

Use the case trace JSON, not the ``.failure.json`` process summary. Seeds reproduce
the generated workload and delay choices. Operating-system scheduling still
varies; replay cannot guarantee the same interleaving.

Start with ``last_progress`` and the worker stack dump for a hang. For accounting
failures, follow matching message identities and operation IDs through invocation
and completion events. Completion timestamps from separate consumers do not
establish receive order. An unbuffered offered value may still be delivered after
closure if a receiver wins the documented race; its sender must then succeed.
``select`` intentionally favors earlier ready cases, so starvation of later
cases alone is not a failure.

Extend the suite
----------------

Add a scenario taking a ``Context`` in ``tests/concurrency/stress/scenarios.py``
and register it in ``SCENARIOS``. Create channels through ``ctx.channel()``, launch
workers through ``ctx.spawn()``, and record operations through ``ctx.op()``.
Use barriers and events for race prerequisites; use seeded per-worker generators
for randomized workload choices. Do not share a random generator between workers.
Join workers through ``ctx.join()`` and add progress checkpoints before potentially
blocking phases.

Assert observable contracts rather than a preferred thread schedule. For an
unfamiliar result, retain its trace and add a small coordinated regression test
before proposing a production fix. The test-only faults verify that accounting,
watchdogs, deadline checks, and observer checks actually detect failures. Passing
stress tests increases confidence but does not prove there are no concurrency bugs.
