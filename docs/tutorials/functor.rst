Build a User Birth-Year Report with ``fmap``
================================================

In this tutorial, you will build a birth-year report for a list of user IDs.
The report will calculate a message for each known user and display a fallback
for each missing user. Along the way, you will use ``fmap`` to transform values
inside ``Maybe`` and ``ImmutableList``.

``Maybe`` and ``ImmutableList`` are functors. This means you can transform
their contents with ``fmap`` while preserving their surrounding structure.

Prerequisites
-------------

- Complete the :doc:`handling-null` tutorial.
- Be familiar with Python functions, lambdas, dictionaries, and type hints.

Step 1: Look Up One User
------------------------

Create a file called ``user_report.py`` with the following contents:

.. code-block:: python

   from katharos.types import Maybe

   users = {
       1: 25,
       2: 30,
       3: 35,
   }

   def get_user_age(user_id: int) -> Maybe[int]:
       return Maybe.from_optional(users.get(user_id))

   print(get_user_age(1))
   print(get_user_age(999))

Run the file:

.. code-block:: bash

   python user_report.py

You should see:

.. code-block:: text

   Just(25)
   Nothing()

The lookup returns ``Just(25)`` for the known user and ``Nothing()`` for the
missing user. This repeats the ``Maybe`` lookup pattern from the previous
tutorial.

Step 2: Transform an Optional Age
---------------------------------

Replace the two ``print`` lines with this code:

.. code-block:: python

   REFERENCE_YEAR = 2026

   birth_year = get_user_age(1).fmap(
       lambda age: REFERENCE_YEAR - age
   )
   missing_birth_year = get_user_age(999).fmap(
       lambda age: REFERENCE_YEAR - age
   )

   print(birth_year)
   print(missing_birth_year)

Run the file again. You should see:

.. code-block:: text

   Just(2001)
   Nothing()

``fmap`` applied the calculation to the age inside ``Just``. It preserved the
``Maybe`` structure, so the result remained a ``Just``. For ``Nothing()``, it
skipped the calculation and preserved ``Nothing()``.

Step 3: Chain Two Transformations
---------------------------------

Keep ``REFERENCE_YEAR`` and replace everything below it with this code:

.. code-block:: python

   message = (
       get_user_age(1)
       .fmap(lambda age: REFERENCE_YEAR - age)
       .fmap(lambda birth_year: f"Born in {birth_year}")
   )
   missing_message = (
       get_user_age(999)
       .fmap(lambda age: REFERENCE_YEAR - age)
       .fmap(lambda birth_year: f"Born in {birth_year}")
   )

   print(message)
   print(missing_message)

Run the file. You should see:

.. code-block:: text

   Just('Born in 2001')
   Nothing()

Each call to ``fmap`` transforms the value produced by the previous call. For
the missing user, both transformations are skipped.

Step 4: Look Up Several Users
-----------------------------

Change the import at the top of ``user_report.py`` to include
``ImmutableList``:

.. code-block:: python

   from katharos.types import ImmutableList, Maybe

Keep the user dictionary, ``get_user_age``, and ``REFERENCE_YEAR``. Replace
everything below ``REFERENCE_YEAR`` with:

.. code-block:: python

   user_ids = ImmutableList([1, 2, 3, 999])
   ages = user_ids.fmap(get_user_age)

   print(ages)

Run the file. You should see:

.. code-block:: text

   ImmutableList([Just(25), Just(30), Just(35), Nothing()])

Here, ``ImmutableList.fmap`` calls ``get_user_age`` for each user ID and
preserves the list structure. The missing user remains visible as
``Nothing()``.

Step 5: Build the Report Pipeline
---------------------------------

Replace the ``user_ids``, ``ages``, and ``print`` lines with this reusable
pipeline:

.. code-block:: python

   def process_user(user_id: int) -> Maybe[str]:
       return (
           get_user_age(user_id)
           .fmap(lambda age: REFERENCE_YEAR - age)
           .fmap(lambda birth_year: f"Born in {birth_year}")
       )

   user_ids = ImmutableList([1, 2, 3, 999])
   results = user_ids.fmap(process_user)

   print(results)

Run the file. You should see:

.. code-block:: text

   ImmutableList([Just('Born in 2001'), Just('Born in 1996'), Just('Born in 1991'), Nothing()])

The outer ``fmap`` processes every user ID in the list. Inside
``process_user``, the two ``Maybe.fmap`` calls build a message only when the
lookup finds an age.

Step 6: Display the Completed Report
------------------------------------

Replace the contents of ``user_report.py`` with the complete program:

.. code-block:: python

   from katharos.types import ImmutableList, Maybe

   REFERENCE_YEAR = 2026

   users = {
       1: 25,
       2: 30,
       3: 35,
   }

   def get_user_age(user_id: int) -> Maybe[int]:
       return Maybe.from_optional(users.get(user_id))

   def process_user(user_id: int) -> Maybe[str]:
       return (
           get_user_age(user_id)
           .fmap(lambda age: REFERENCE_YEAR - age)
           .fmap(lambda birth_year: f"Born in {birth_year}")
       )

   def format_result(message: Maybe[str]) -> str:
       return message.unwrap_or("User not found")

   user_ids = ImmutableList([1, 2, 3, 999])
   results = user_ids.fmap(process_user)
   formatted_results = results.fmap(format_result)

   for result in formatted_results:
       print(result)

Run the completed report:

.. code-block:: bash

   python user_report.py

You should see:

.. code-block:: text

   Born in 2001
   Born in 1996
   Born in 1991
   User not found

The pipeline preserves each ``Maybe`` until ``format_result`` converts it to
displayable text. The second ``ImmutableList.fmap`` then applies that boundary
conversion to every report entry.

What You Built
--------------

You built a birth-year report that:

- Reuses ``Maybe.from_optional`` to represent successful and missing lookups.
- Transforms values inside ``Maybe`` without explicit ``None`` checks.
- Chains several ``Maybe.fmap`` transformations.
- Uses ``ImmutableList.fmap`` to process several users.
- Converts each final ``Maybe`` to displayable text with ``unwrap_or``.

Next Steps
----------

- Continue with :doc:`monadic-computation` to chain operations that themselves
  return ``Maybe``.
- Read :doc:`../explanation/functors-mathematics` to understand functors and
  their laws.
- Consult :doc:`../reference/operators` for the ``fmap`` contract and related
  operations.
