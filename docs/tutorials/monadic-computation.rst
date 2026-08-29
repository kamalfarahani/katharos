Compose ``Maybe``-Returning Functions with Bind
===============================================

In this tutorial, you will build a contact lookup by composing two functions
that can fail. The first function will find a username from a user ID. The
second will find an email address from that username. You will use ``|``
(bind) to connect them without producing nested ``Maybe`` values.

**Time:** About 15 minutes.

Prerequisites
-------------

- Complete the :doc:`functor` tutorial.
- Be familiar with Python functions, dictionaries, and type hints.

Step 1: Create Two Independent Lookups
--------------------------------------

Create a file called ``contact_lookup.py`` with the following contents:

.. code-block:: python

   from katharos.types import Maybe

   USERNAMES = {
       1: "alice",
       2: "bob",
   }

   EMAILS = {
       "alice": "alice@example.com",
   }

   def find_username(user_id: int) -> Maybe[str]:
       return Maybe.from_optional(USERNAMES.get(user_id))

   def find_email(username: str) -> Maybe[str]:
       return Maybe.from_optional(EMAILS.get(username))

   print(find_username(1))
   print(find_email("alice"))

Run the file:

.. code-block:: bash

   python contact_lookup.py

You should see:

.. code-block:: text

   Just('alice')
   Just('alice@example.com')

Each lookup accepts a plain value and returns a ``Maybe``. It returns ``Just``
when it finds a match and ``Nothing()`` when it does not.

Step 2: See the Composition Gap
-------------------------------

The two functions have these type shapes:

.. code-block:: python

   find_username: int -> Maybe[str]
   find_email:    str -> Maybe[str]

Ordinary function composition cannot pass the result of ``find_username``
directly to ``find_email``. The first function returns ``Maybe[str]``, but the
second requires a plain ``str``.

Use ``fmap`` from the previous tutorial to apply ``find_email`` to the wrapped
username. Replace the two ``print`` lines with:

.. code-block:: python

   username = find_username(1)
   nested_email = username.fmap(find_email)

   print(nested_email)

Run the file again. You should see:

.. code-block:: text

   Just(Just('alice@example.com'))

``fmap`` preserves the outer ``Maybe``. Because ``find_email`` also returns a
``Maybe``, the composed result contains one ``Maybe`` inside another.

Step 3: Connect the Functions with Bind
---------------------------------------

Replace the ``nested_email`` and ``print`` lines with:

.. code-block:: python

   email = username | find_email

   print(email)

Run the file. You should see:

.. code-block:: text

   Just('alice@example.com')

The ``|`` operator calls ``username.bind(find_email)``. Bind passes the plain
username to ``find_email`` and directly uses the ``Maybe`` returned by that
function. The result stays flat.

Here, bind connects a ``Maybe[B]`` value to a function with the shape
``B -> Maybe[C]``. In the next step, you will place this expression inside a
new function to compose ``A -> Maybe[B]`` with ``B -> Maybe[C]``.

Step 4: Create a Reusable Composed Function
-------------------------------------------

Replace the ``username``, ``email``, and ``print`` lines with:

.. code-block:: python

   def find_user_email(user_id: int) -> Maybe[str]:
       return find_username(user_id) | find_email

   print(find_user_email(1))

Run the file. You should see:

.. code-block:: text

   Just('alice@example.com')

``find_user_email`` passes the plain user ID to ``find_username``. It then
binds the returned ``Maybe[str]`` to ``find_email``. If the first lookup
returns ``Nothing()``, bind skips the second lookup.

You have composed the two original functions into a new function with this
type shape:

.. code-block:: text

   find_user_email: int -> Maybe[str]

.. note::

   Keeping functions composable while their results remain inside ``Maybe``
   is the practical job a monad is designed to do.

Step 5: Run the Complete Contact Lookup
---------------------------------------

Replace the contents of ``contact_lookup.py`` with the complete program:

.. code-block:: python

   from katharos.types import Maybe

   USERNAMES = {
       1: "alice",
       2: "bob",
   }

   EMAILS = {
       "alice": "alice@example.com",
   }

   def find_username(user_id: int) -> Maybe[str]:
       return Maybe.from_optional(USERNAMES.get(user_id))

   def find_email(username: str) -> Maybe[str]:
       return Maybe.from_optional(EMAILS.get(username))

   def find_user_email(user_id: int) -> Maybe[str]:
       return find_username(user_id) | find_email

   for user_id in (1, 2, 999):
       print(f"{user_id}: {find_user_email(user_id)}")

Run the completed lookup:

.. code-block:: bash

   python contact_lookup.py

You should see:

.. code-block:: text

   1: Just('alice@example.com')
   2: Nothing()
   999: Nothing()

User ``1`` completes both lookups. User ``2`` has a username but no email, so
``find_email`` returns ``Nothing()``. User ``999`` is missing from the first
lookup, so bind skips ``find_email`` and preserves ``Nothing()``.

What You Built
--------------

You built a contact lookup that:

- Defines two independently useful functions that return ``Maybe``.
- Uses bind to compose ``A -> Maybe[B]`` with ``B -> Maybe[C]``.
- Produces a reusable ``A -> Maybe[C]`` function without nested values.
- Stops the composed lookup as soon as any function returns ``Nothing()``.

Next Steps
----------

- Continue with :doc:`do-syntax` to express larger bind chains more clearly.
- Read :doc:`../explanation/monads-mathematics` for Kleisli composition and
  the monad laws.
- Consult :doc:`../reference/operators` for the ``|`` contract and related
  operations.
