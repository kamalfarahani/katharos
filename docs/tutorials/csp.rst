Porting Go's Worker Pool
========================

In this tutorial, we will port the classic *worker pool* program from `Go by Example <https://gobyexample.com/worker-pools>`_ to Python using Katharos' CSP (Communicating Sequential Processes) primitives. A worker pool is a fixed set of concurrent workers that pull tasks from a shared queue, do them, and push results to another queue. Along the way we will use ``Channel`` to move values between threads, ``csp.go`` to run the workers concurrently, and a structured-concurrency scope to wait for them to finish.

Here is the original Go program we are porting:

.. code-block:: go

   func worker(id int, jobs <-chan int, results chan<- int) {
       for j := range jobs {
           results <- j * 2
       }
   }

   func main() {
       const numJobs = 5
       jobs := make(chan int, numJobs)
       results := make(chan int, numJobs)

       for w := 1; w <= 3; w++ {
           go worker(w, jobs, results)
       }

       for j := 1; j <= numJobs; j++ {
           jobs <- j
       }
       close(jobs)

       for a := 1; a <= numJobs; a++ {
           <-results
       }
   }

Prerequisites
-------------

- Python 3.13 or later
- Katharos installed (see :doc:`getting-started`)
- Complete the :doc:`error-handling` tutorial so you are familiar with
  ``Result``.

Step 1: Write the Worker
------------------------

A worker reads jobs from one channel and writes results to another. In Go this is ``for j := range jobs``; in Katharos a channel is iterable, so it is a plain ``for`` loop that ends when the channel is closed. We will start with a single worker to keep the output easy to follow.

Create a new file called ``pool.py`` with the following contents:

.. code-block:: python

   from katharos.concurrency.csp import Channel, csp

   def worker(jobs: Channel[int], results: Channel[int]) -> None:
       for job in jobs:
           results.send(job * 2)

   jobs: Channel[int] = csp.Channel[int](capacity=3)
   results: Channel[int] = csp.Channel[int](capacity=3)

   for j in [1, 2, 3]:
       jobs.send(j)
   jobs.close()

   csp.go(worker, jobs, results)

   for _ in range(3):
       print(results.recv().unwrap())

Run the file:

.. code-block:: bash

   python pool.py

You should see:

.. code-block:: text

   2
   4
   6

Notice the shape of the port. ``make(chan int, numJobs)`` becomes ``csp.Channel[int](capacity=3)``, ``go worker(...)`` becomes ``csp.go(worker, ...)``, and ``close(jobs)`` becomes ``jobs.close()``. Because ``recv`` returns a ``Result``, we call ``unwrap`` to get the plain value.

Step 2: Scale Up to a Pool
--------------------------

The point of a worker pool is to run several workers against the *same* jobs channel, so they share the work. We will start three workers and feed them five jobs. Replace the contents of ``pool.py`` with:

.. code-block:: python

   from katharos.concurrency.csp import Channel, csp

   def worker(jobs: Channel[int], results: Channel[int]) -> None:
       for job in jobs:
           results.send(job * 2)

   num_jobs: int = 5
   jobs: Channel[int] = csp.Channel[int](capacity=num_jobs)
   results: Channel[int] = csp.Channel[int](capacity=num_jobs)

   for _ in range(3):
       csp.go(worker, jobs, results)

   for j in range(1, num_jobs + 1):
       jobs.send(j)
   jobs.close()

   collected: list[int] = [results.recv().unwrap() for _ in range(num_jobs)]
   print(sorted(collected))

Run the file:

.. code-block:: bash

   python pool.py

You should see:

.. code-block:: text

   [2, 4, 6, 8, 10]

Notice that all three workers read from one shared ``jobs`` channel, so each job is handled by exactly one worker. Because the workers run concurrently, the results can arrive in any order, so we ``sorted`` them before printing. Closing ``jobs`` is what tells every worker's ``for`` loop to stop.

Step 3: See the Workers Run in Parallel
---------------------------------------

So far the work has been instant. Let us make each job take a tenth of a second, so we can see the pool actually working in parallel. We will also use ``csp.go`` as a ``with`` block: a structured-concurrency scope that waits for every worker launched inside it to finish before moving on. Replace the contents of ``pool.py`` with:

.. code-block:: python

   import time

   from katharos.concurrency.csp import Channel, csp

   def worker(jobs: Channel[int], results: Channel[int]) -> None:
       for job in jobs:
           time.sleep(0.1)
           results.send(job * 2)

   num_jobs: int = 5
   jobs: Channel[int] = csp.Channel[int](capacity=num_jobs)
   results: Channel[int] = csp.Channel[int](capacity=num_jobs)

   for j in range(1, num_jobs + 1):
       jobs.send(j)
   jobs.close()

   start = time.monotonic()
   with csp.go:
       for _ in range(3):
           csp.go(worker, jobs, results)
   elapsed = time.monotonic() - start

   results.close()
   print(sorted(results))
   print(f"finished in under half a second: {elapsed < 0.5}")

Run the file:

.. code-block:: bash

   python pool.py

You should see:

.. code-block:: text

   [2, 4, 6, 8, 10]
   finished in under half a second: True

Notice the speedup. Five jobs at a tenth of a second each would take half a second one at a time, but three workers share the load and finish in about two tenths of a second. The ``with csp.go`` block does the waiting for us: once it exits, every worker has finished, so it is safe to ``close`` the results channel and drain it with ``sorted``.

If your program hangs here, check that you closed ``jobs`` (otherwise the workers' ``for`` loops never end) and that ``results`` has enough ``capacity`` to hold every result.

What We Built
-------------

We ported Go's worker-pool program to Katharos and watched it process jobs across three concurrent workers. The translation is almost one to one:

.. list-table::
   :header-rows: 1

   * - Go
     - Katharos
   * - ``make(chan int, n)``
     - ``csp.Channel[int](capacity=n)``
   * - ``go worker(...)``
     - ``csp.go(worker, ...)``
   * - ``for j := range jobs``
     - ``for job in jobs``
   * - ``close(jobs)``
     - ``jobs.close()``
   * - ``<-results``
     - ``results.recv()`` (returns a ``Result``)

The one idea Katharos adds is the ``with csp.go`` scope, which joins all the work launched inside it so you never have to track and wait on individual workers by hand. With channels for communication and goroutines for concurrency, you coordinate work by passing messages instead of sharing and locking state.
