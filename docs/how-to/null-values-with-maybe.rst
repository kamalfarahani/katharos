How to Handle Null Values with Maybe
======================================

This guide covers practical patterns for replacing ``None``-returning code with ``Maybe``, propagating absence through pipelines, and safely extracting values - without scattering ``if x is not None`` checks across your codebase.

Prerequisites
-------------

- Familiarity with ``Maybe.Just`` / ``Maybe.Nothing`` and the ``|`` operator

Wrapping a function that returns None
--------------------------------------

Convert any function that returns ``None`` on absence into one that returns ``Maybe``:

.. code-block:: python

   from katharos.types import Maybe

   def find_user(uid: int) -> Maybe[dict]:
       db = {
           1: {"name": "Alice", "department": "engineering"},
           2: {"name": "Bob"},
       }
       user = db.get(uid)
       return Maybe[dict].Just(user) if user is not None else Maybe[dict].Nothing()

Call it the same way you would before - but now the absence is explicit in the type:

.. code-block:: python

   find_user(1)   # Just({'name': 'Alice'})
   find_user(99)  # Nothing()

Transforming a value inside Maybe
-----------------------------------

Use ``fmap`` to apply a function to the wrapped value. If the ``Maybe`` is ``Nothing``, ``fmap`` does nothing and propagates the absence:

.. code-block:: python

   find_user(1).fmap(lambda u: u["name"])   # Just('Alice')
   find_user(99).fmap(lambda u: u["name"])  # Nothing()

Chaining operations that may also be absent
--------------------------------------------

Use ``|`` (``bind``) when the next step itself returns a ``Maybe``. The chain short-circuits on the first ``Nothing``:

.. code-block:: python

   def get_email(user: dict) -> Maybe[str]:
       email = user.get("email")
       return Maybe[str].Just(email) if email is not None else Maybe[str].Nothing()

   find_user(1) | get_email   # Nothing() - Alice has no email field
   find_user(99) | get_email  # Nothing() - user not found

Providing a default when absent
---------------------------------

Check the result with ``is_just()`` and call ``unwrap()`` to get the value, or supply a fallback:

.. code-block:: python

   result = find_user(1).fmap(lambda u: u["name"])
   name = result.unwrap() if result.is_just() else "Guest"
   print(name)  # Alice

   result = find_user(99).fmap(lambda u: u["name"])
   name = result.unwrap() if result.is_just() else "Guest"
   print(name)  # Guest

Flattening multi-step lookups with do-notation
------------------------------------------------

When several steps each return a ``Maybe`` and each depends on the previous result, use the ``@do`` decorator to write them as a plain sequence. The first ``Nothing`` short-circuits the whole block:

.. code-block:: python

   from katharos.syntax_sugar import do, DoBlock

   def get_department(user: dict) -> Maybe[str]:
       dept = user.get("department")
       return Maybe[str].Just(dept) if dept is not None else Maybe[str].Nothing()

   def get_budget(dept: str) -> Maybe[int]:
       budgets = {"engineering": 50000, "marketing": 30000}
       b = budgets.get(dept)
       return Maybe[int].Just(b) if b is not None else Maybe[int].Nothing()

   @do(Maybe)
   def user_budget(uid: int) -> DoBlock[Maybe, int]:
       user:   dict = yield find_user(uid)
       dept:   str  = yield get_department(user)
       budget: int  = yield get_budget(dept)
       return budget

   user_budget(1)   # Just(50000) - Alice is in engineering
   user_budget(2)   # Nothing() - Bob has no department
   user_budget(99)  # Nothing() - user not found

Combining multiple lookups
--------------------------

When a result depends on several lookups all succeeding, use ``@do`` rather than
checking ``is_just()`` on each result manually:

.. code-block:: python

   @do(Maybe)
   def greet(uid: int, greeting_id: int) -> DoBlock[Maybe, str]:
       greetings = {1: "Hello", 2: "Hi"}

       def get_greeting(g_id: int) -> Maybe[str]:
           g = greetings.get(g_id)
           return Maybe[str].Just(g) if g is not None else Maybe[str].Nothing()

       user:     dict = yield find_user(uid)
       greeting: str  = yield get_greeting(greeting_id)
       return f"{greeting}, {user['name']}!"

   greet(1, 1)   # Just('Hello, Alice!')
   greet(1, 99)  # Nothing() - greeting not found
   greet(99, 1)  # Nothing() - user not found

Related Guides
--------------

- :doc:`error-handling` - when you need to attach an error message to an absence, convert ``Maybe`` to ``Result``
- :doc:`do-notation` - deeper examples of do-notation with ``Maybe`` and ``Result``
- :doc:`chain-operations` - composing longer pipelines with ``|`` and ``>>``

