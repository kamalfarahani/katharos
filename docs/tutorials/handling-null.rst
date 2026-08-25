Handle Missing User Data with Maybe
===================================

In this tutorial, you will build a user lookup that handles both existing and
missing users without returning ``None``. You will create ``Just`` and
``Nothing`` values, convert an optional Python value into a ``Maybe``, and
provide a safe fallback for display.

**Time:** About 10 minutes

Prerequisites
-------------

- Complete the :doc:`getting-started` tutorial.
- Be familiar with Python dictionaries, functions, and type hints.

Step 1: Represent Present and Missing Values
--------------------------------------------

Create a file called ``user_lookup.py`` with the following contents:

.. code-block:: python

   from katharos.types import Maybe

   found = Maybe[str].Just("Alice")
   missing = Maybe[str].Nothing()

   print(found)
   print(missing)

Run the file:

.. code-block:: bash

   python user_lookup.py

You should see:

.. code-block:: text

   Just('Alice')
   Nothing()

``Just`` contains the user's name. ``Nothing`` represents a missing name.

.. note::

   This tutorial uses an explicit type argument, such as ``Maybe[str]``, when
   constructing values. This helps a type checker infer what the ``Maybe`` can
   contain.

Step 2: Build a User Lookup
---------------------------

Replace the contents of ``user_lookup.py`` with this user dictionary and
lookup function:

.. code-block:: python

   from katharos.types import Maybe

   users: dict[int, str] = {
       1: "Alice",
       2: "Bob",
       3: "Charlie",
   }

   def find_user(user_id: int) -> Maybe[str]:
       return Maybe.from_optional(users.get(user_id))

   found = find_user(1)
   print(found)

Run the file again:

.. code-block:: bash

   python user_lookup.py

You should see:

.. code-block:: text

   Just('Alice')

The dictionary's ``get`` method returns either a name or ``None``.
``Maybe.from_optional`` converts those two possibilities into ``Just`` or
``Nothing``.

Step 3: Look Up a Missing User
------------------------------

Add these lines to the bottom of ``user_lookup.py``:

.. code-block:: python

   missing = find_user(99)
   print(missing)

Run the file:

.. code-block:: bash

   python user_lookup.py

You should see:

.. code-block:: text

   Just('Alice')
   Nothing()

The same function now represents both lookup outcomes without returning
``None`` to its caller.

Step 4: Display a Safe Fallback
-------------------------------

Replace the contents of ``user_lookup.py`` with the complete program:

.. code-block:: python

   from katharos.types import Maybe

   users: dict[int, str] = {
       1: "Alice",
       2: "Bob",
       3: "Charlie",
   }

   def find_user(user_id: int) -> Maybe[str]:
       return Maybe.from_optional(users.get(user_id))

   def display_user(user_id: int) -> str:
       return find_user(user_id).unwrap_or("User not found")

   print(display_user(1))
   print(display_user(99))

Run the completed program:

.. code-block:: bash

   python user_lookup.py

You should see:

.. code-block:: text

   Alice
   User not found

``unwrap_or`` returns the contained name when one exists. For ``Nothing``, it
returns the fallback string instead.

What You Built
--------------

You built a user lookup that:

- Represents an existing value with ``Just`` and a missing value with
  ``Nothing``.
- Converts a Python optional value with ``Maybe.from_optional``.
- Produces displayable text with ``unwrap_or``.

Next Steps
----------

- Continue with :doc:`functor` to transform values inside ``Maybe``.
- See :doc:`../how-to/null-values-with-maybe` for practical null-handling
  patterns after you complete the introductory tutorials.
- Consult the :doc:`../reference/api/types` for the complete ``Maybe`` API.
