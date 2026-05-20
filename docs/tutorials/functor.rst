Build a Data Processing Pipeline with Functors
==============================================

In this tutorial, we will build a data processing pipeline that transforms values inside containers. By the end, you will have a working system that processes user data using ``Maybe`` and ``ImmutableList``.

Step 1: Transform a Single Optional Value
------------------------------------------

First, we will transform a value inside a ``Maybe``. Create a new Python file called ``pipeline.py`` and add this code:

.. code-block:: python

   from katharos.types import Maybe

   age = Maybe[int].Just(25)
   doubled = age.fmap(lambda x: x * 2)
   print(doubled)

Run this code. You should see ``Just(50)``. The value was doubled.

Now try with an empty ``Maybe``:

.. code-block:: python

   age = Maybe[int].Nothing()
   doubled = age.fmap(lambda x: x * 2)
   print(doubled)

You should see ``Nothing()``. The function was not called because there was no value to transform.

Step 2: Process User Ages
--------------------------

Now we will build a function that processes user ages. Add this code:

.. code-block:: python

   def get_user_age(user_id: int) -> Maybe[int]:
       users = {1: 25, 2: 30, 3: 35}
       age = users.get(user_id)
       if age is None:
           return Maybe[int].Nothing()
       return Maybe[int].Just(age)

   age = get_user_age(1)
   print(age)

You should see ``Just(25)``.

Now transform the age to calculate birth year:

.. code-block:: python

   current_year = 2026
   birth_year = get_user_age(1).fmap(lambda age: current_year - age)
   print(birth_year)

You should see ``Just(2001)``. The birth year was calculated.

Try with a user that doesn't exist:

.. code-block:: python

   birth_year = get_user_age(999).fmap(lambda age: current_year - age)
   print(birth_year)

You should see ``Nothing()``.

Step 3: Chain Multiple Transformations
---------------------------------------

We will now chain multiple transformations together. Add this code:

.. code-block:: python

   result = (
       get_user_age(2)
       .fmap(lambda age: age + 5)
       .fmap(lambda age: age * 2)
       .fmap(lambda age: f"Age in dog years: {age}")
   )
   print(result)

You should see ``Just('Age in dog years: 70')``. Each transformation was applied in sequence.

Try with a missing user:

.. code-block:: python

   result = (
       get_user_age(999)
       .fmap(lambda age: age + 5)
       .fmap(lambda age: age * 2)
       .fmap(lambda age: f"Age in dog years: {age}")
   )
   print(result)

You should see ``Nothing()``. All transformations were skipped.

Step 4: Transform Multiple Values in a List
--------------------------------------------

Now we will transform all values in an ``ImmutableList``. Add this code:

.. code-block:: python

   from katharos.types import ImmutableList

   ages = ImmutableList([20, 25, 30, 35, 40])
   doubled = ages.fmap(lambda x: x * 2)
   print(doubled)

You should see ``ImmutableList([40, 50, 60, 70, 80])``. The function was applied to every element.

Try with an empty list:

.. code-block:: python

   ages = ImmutableList([])
   doubled = ages.fmap(lambda x: x * 2)
   print(doubled)

You should see ``ImmutableList([])``. There were no elements to transform.

Step 5: Process a List of User IDs
-----------------------------------

We will now process multiple user IDs at once. Add this code:

.. code-block:: python

   user_ids = ImmutableList([1, 2, 3])
   ages = user_ids.fmap(lambda user_id: get_user_age(user_id))
   print(ages)

You should see ``ImmutableList([Just(25), Just(30), Just(35)])``. Each user ID was transformed into a ``Maybe`` containing their age.

Now extract just the birth years:

.. code-block:: python

   current_year = 2026
   birth_years = user_ids.fmap(
       lambda user_id: get_user_age(user_id).fmap(lambda age: current_year - age)
   )
   print(birth_years)

You should see ``ImmutableList([Just(2001), Just(1996), Just(1991)])``.

Step 6: Build a Complete Processing Pipeline
---------------------------------------------

Now we will combine everything into a complete pipeline. Add this code:

.. code-block:: python

   def process_user(user_id: int) -> Maybe[str]:
       current_year = 2026
       return (
           get_user_age(user_id)
           .fmap(lambda age: current_year - age)
           .fmap(lambda birth_year: f"Born in {birth_year}")
       )

   user_ids = ImmutableList([1, 2, 3, 999])
   results = user_ids.fmap(process_user)
   print(results)

You should see ``ImmutableList([Just('Born in 2001'), Just('Born in 1996'), Just('Born in 1991'), Nothing()])``. Each user was processed, and the missing user resulted in ``Nothing()``.

Step 7: Format the Output
--------------------------

We will now format the results for display. Add this code:

.. code-block:: python

   def format_result(maybe_message: Maybe[str]) -> str:
       if maybe_message.is_just():
           return maybe_message.value
       return "User not found"

   formatted = results.fmap(format_result)
   print(formatted)

You should see ``ImmutableList(['Born in 2001', 'Born in 1996', 'Born in 1991', 'User not found'])``.

Print each result on a separate line:

.. code-block:: python

   for message in formatted:
       print(message)

You should see:

.. code-block:: text

   Born in 2001
   Born in 1996
   Born in 1991
   User not found

Step 8: Add Data Validation
----------------------------

We will now add validation to reject invalid ages. Add this code:

.. code-block:: python

   def get_user_age_safe(user_id: int) -> Maybe[int]:
       users = {1: 25, 2: 30, 3: 200}
       age = users.get(user_id)
       if age is None or age < 0 or age > 150:
           return Maybe[int].Nothing()
       return Maybe[int].Just(age)

   ages = ImmutableList([1, 2, 3]).fmap(get_user_age_safe)
   print(ages)

You should see ``ImmutableList([Just(25), Just(30), Nothing()])``. The invalid age (200) was rejected.

Now use this in the full pipeline:

.. code-block:: python

   def process_user_safe(user_id: int) -> Maybe[str]:
       current_year = 2026
       return (
           get_user_age_safe(user_id)
           .fmap(lambda age: current_year - age)
           .fmap(lambda birth_year: f"Born in {birth_year}")
       )

   user_ids = ImmutableList([1, 2, 3])
   results = user_ids.fmap(process_user_safe)
   print(results)

You should see ``ImmutableList([Just('Born in 2001'), Just('Born in 1996'), Nothing()])``.

What We Built
-------------

We built a complete data processing pipeline that:

- Transforms values inside ``Maybe`` containers
- Chains multiple transformations together
- Processes lists of values with ``ImmutableList``
- Handles missing data gracefully
- Validates input data