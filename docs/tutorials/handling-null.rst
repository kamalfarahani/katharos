Handling Null Values with Maybe
================================

In this tutorial, we will build a program that safely looks up users and their friends without writing a single ``None`` check. Along the way, we will encounter ``Maybe[T].Just``, ``Maybe[T].Nothing``, ``fmap``, and the ``|`` (bind) operator.

.. note::

   Always supply a type argument when constructing a ``Maybe`` value - use ``Maybe[str].Just("hello")`` and ``Maybe[str].Nothing()``, not ``Maybe.Just("hello")`` or ``Maybe.Nothing()``. The type argument lets your type checker (e.g. Pyright or mypy) infer the element type of the container and catch errors at development time.

Prerequisites
-------------

- Python 3.13 or later
- Katharos installed (see :doc:`getting-started`)

Step 1: Look Up a User
----------------------

Create a file called ``user_lookup.py`` with the following contents:

.. code-block:: python

   from katharos.types import Maybe

   users = {
       1: "Alice",
       2: "Bob",
       3: "Charlie"
   }

   def find_user(user_id: int) -> Maybe[str]:
       if user_id in users:
           return Maybe[str].Just(users[user_id])
       else:
           return Maybe[str].Nothing()

   result = find_user(1)
   print(result)

Now run the file:

.. code-block:: bash

   python user_lookup.py

You should see:

.. code-block:: text

   Just(Alice)

Notice the result is wrapped in ``Just(...)`` instead of being a plain string.

Step 2: Handle the Missing Case
--------------------------------

Now we will look up a user that doesn't exist. Add these two lines at the bottom of ``user_lookup.py``:

.. code-block:: python

   missing = find_user(99)
   print(missing)

Run the file again:

.. code-block:: bash

   python user_lookup.py

You should see:

.. code-block:: text

   Just(Alice)
   Nothing()

Notice that the missing user is represented as ``Nothing()`` instead of raising an error or returning ``None``.

Step 3: Transform the Value with fmap
--------------------------------------

Instead of checking if the value exists, we can transform it directly. Replace the four lines at the bottom of ``user_lookup.py`` with:

.. code-block:: python

   result = find_user(1)
   greeting = result.fmap(lambda name: f"Hello, {name}!")
   print(greeting)

   missing = find_user(99)
   missing_greeting = missing.fmap(lambda name: f"Hello, {name}!")
   print(missing_greeting)

Run the file:

.. code-block:: bash

   python user_lookup.py

You should see:

.. code-block:: text

   Just(Hello, Alice!)
   Nothing()

Notice how the transformation only happens when the value exists. When the Maybe is Nothing, the function is never called.

Step 4: Chain Operations Together
----------------------------------

Now we will look up a user and then look up their friend. First, add a ``friends`` dictionary and a ``find_friend`` function below the existing ``find_user`` function:

.. code-block:: python

   friends = {
       "Alice": "Bob",
       "Bob": "Charlie",
       "Charlie": "Alice"
   }

   def find_friend(name: str) -> Maybe[str]:
       if name in friends:
           return Maybe[str].Just(friends[name])
       else:
           return Maybe[str].Nothing()

Now replace the six lines at the bottom of the file with:

.. code-block:: python

   result = find_user(1)
   friend = result | find_friend
   print(friend)

   missing = find_user(99)
   missing_friend = missing | find_friend
   print(missing_friend)

Run the file:

.. code-block:: bash

   python user_lookup.py

You should see:

.. code-block:: text

   Just(Bob)
   Nothing()

We used the ``|`` operator to chain ``find_friend`` after ``find_user``. The chain stops at the first ``Nothing()`` and skips ``find_friend`` entirely.

What We Built
-------------

We wrote a program that looks up users and their friends without a single ``None`` check or ``try/except`` block. The Maybe type carried the "missing" case through every transformation for us.
