Build a Data Processing Pipeline with Functors
==============================================

In this tutorial, we will build a data processing pipeline that transforms values inside containers. Along the way, we will encounter ``fmap`` on ``Maybe`` and ``ImmutableList``, and learn how transformations compose cleanly when data may be missing.

Prerequisites
-------------

- Complete the :doc:`getting-started` tutorial.
- Katharos installed (see :doc:`getting-started`)

Step 1: Transform a Single Optional Value
------------------------------------------

Create a new Python file called ``pipeline.py`` with the following contents:

.. code-block:: python

   from katharos.types import Maybe

   age = Maybe[int].Just(25)
   doubled = age.fmap(lambda x: x * 2)
   print(doubled)

   age = Maybe[int].Nothing()
   doubled = age.fmap(lambda x: x * 2)
   print(doubled)

Run the file:

.. code-block:: bash

   python pipeline.py

You should see:

.. code-block:: text

   Just(50)
   Nothing()

Notice that the value was doubled in the first case. In the second case the function was not called at all - there was no value to transform.

Step 2: Process User Ages
--------------------------

Now we will build a function that looks up user ages. Replace the contents of ``pipeline.py`` with:

.. code-block:: python

   from katharos.types import Maybe

   def get_user_age(user_id: int) -> Maybe[int]:
       users = {1: 25, 2: 30, 3: 35}
       age = users.get(user_id)
       if age is None:
           return Maybe[int].Nothing()
       return Maybe[int].Just(age)

   current_year = 2026
   birth_year = get_user_age(1).fmap(lambda age: current_year - age)
   print(birth_year)

   birth_year = get_user_age(999).fmap(lambda age: current_year - age)
   print(birth_year)

Run the file:

.. code-block:: bash

   python pipeline.py

You should see:

.. code-block:: text

   Just(2001)
   Nothing()

Notice how the birth year calculation is skipped entirely when the user does not exist.

Step 3: Chain Multiple Transformations
---------------------------------------

We will now chain multiple transformations together. Add this code at the bottom of ``pipeline.py``:

.. code-block:: python

   result = (
       get_user_age(2)
       .fmap(lambda age: age + 5)
       .fmap(lambda age: age * 2)
       .fmap(lambda age: f"Age in dog years: {age}")
   )
   print(result)

   result = (
       get_user_age(999)
       .fmap(lambda age: age + 5)
       .fmap(lambda age: age * 2)
       .fmap(lambda age: f"Age in dog years: {age}")
   )
   print(result)

Run the file:

.. code-block:: bash

   python pipeline.py

You should see the new lines at the bottom of the output:

.. code-block:: text

   Just('Age in dog years: 70')
   Nothing()

Notice that all three transformations were skipped for the missing user. Each transformation preserves the ``Nothing()`` without any extra checking.

Step 4: Transform Multiple Values in a List
--------------------------------------------

Now we will transform all values in an ``ImmutableList``. Add this code at the bottom of ``pipeline.py``:

.. code-block:: python

   from katharos.types import ImmutableList

   ages = ImmutableList([20, 25, 30, 35, 40])
   doubled = ages.fmap(lambda x: x * 2)
   print(doubled)

Run the file. You should see a new line at the bottom:

.. code-block:: text

   ImmutableList([40, 50, 60, 70, 80])

Notice that ``fmap`` applied the function to every element, producing a new list.

Step 5: Process a List of User IDs
-----------------------------------

We will now process multiple user IDs at once. Add this code at the bottom of ``pipeline.py``:

.. code-block:: python

   user_ids = ImmutableList([1, 2, 3])
   current_year = 2026
   birth_years = user_ids.fmap(
       lambda user_id: get_user_age(user_id).fmap(lambda age: current_year - age)
   )
   print(birth_years)

Run the file. You should see:

.. code-block:: text

   ImmutableList([Just(2001), Just(1996), Just(1991)])

Notice how ``fmap`` composes: the outer ``fmap`` iterates over the list, and the inner ``fmap`` transforms each ``Maybe`` age into a birth year.

Step 6: Build a Complete Processing Pipeline
---------------------------------------------

Now we will combine everything into a reusable pipeline function. Add this code at the bottom of ``pipeline.py``:

.. code-block:: python

   def process_user(user_id: int) -> Maybe[str]:
       current_year = 2026
       return (
           get_user_age(user_id)
           .fmap(lambda age: current_year - age)
           .fmap(lambda birth_year: f"Born in {birth_year}")
       )

   def format_result(maybe_message: Maybe[str]) -> str:
       if maybe_message.is_just():
           return maybe_message.value
       return "User not found"

   user_ids = ImmutableList([1, 2, 3, 999])
   results = user_ids.fmap(process_user)
   formatted = results.fmap(format_result)

   for message in formatted:
       print(message)

Run the file. The final lines of the output should be:

.. code-block:: text

   Born in 2001
   Born in 1996
   Born in 1991
   User not found

Notice that the missing user (ID 999) produced the fallback string ``"User not found"`` - the ``Maybe`` propagated through the whole pipeline and was only converted to a plain value at the very end.

What We Built
-------------

We built a data processing pipeline that transforms values inside ``Maybe`` and ``ImmutableList`` containers using ``fmap``. The same operator works on both types, and transformations compose cleanly without any explicit ``None`` checks.
