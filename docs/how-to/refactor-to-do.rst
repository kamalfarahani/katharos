How to Refactor Bind Chains to Do-Notation
==========================================

This guide shows you how to convert a nested bind chain - with multiple lambdas capturing outer values - into equivalent do-notation that is easier to read and modify.

Prerequisites
-------------

- Existing code that uses the ``|`` bind operator across 3 or more steps
- Familiarity with :doc:`do-notation`

When to refactor
-----------------

Refactor to do-notation when you have:

- **3 or more chained ``|`` calls** where inner lambdas need values from outer lambdas
- **Intermediate values reused** across multiple steps
- **Deeply nested lambdas** that obscure what the code is computing

Do not refactor if you have a simple linear chain where each step does not capture a previous result - the ``|`` form is already concise there.

Step 1: Identify the nested capture pattern
--------------------------------------------

This is the signal: a lambda inside a lambda captures an outer variable.

.. code-block:: python

   from katharos.types import Maybe

   def find_user(uid: int) -> Maybe[dict]:
       users = {1: {"name": "Alice", "team_id": 10}}
       return Maybe[dict].Just(users[uid]) if uid in users else Maybe[dict].Nothing()

   def find_team(tid: int) -> Maybe[dict]:
       teams = {10: {"name": "Engineering", "budget": 50_000}}
       return Maybe[dict].Just(teams[tid]) if tid in teams else Maybe[dict].Nothing()

   def budget_report(user: dict, team: dict) -> str:
       return f"{user['name']} is in {team['name']} with budget {team['budget']}"

   # Before: nested lambda captures `user` from outer scope
   result = (
       find_user(1)
       | (lambda user:
           find_team(user["team_id"])
           | (lambda team:
               Maybe[str].Just(budget_report(user, team))
           )
       )
   )

The inner lambda captures ``user`` from the outer lambda. This nesting grows with every additional value you need.

Step 2: Replace with @do(M)
----------------------------

Each ``lambda x: ...`` in the bind chain maps directly to a ``yield`` expression. Because ``yield`` returns the real unwrapped value, you can use it on the very next line - including indexing it, calling methods on it, or passing it to another monadic function:

.. code-block:: python

   from katharos.syntax_sugar import do, DoBlock

   @do(Maybe)
   def block() -> DoBlock[Maybe, str]:
       user: dict = yield find_user(1)
       team: dict = yield find_team(user["team_id"])  # user is the real dict here
       return budget_report(user, team)

   result = block()

Notice that ``user["team_id"]`` works directly inside the block - no pre-computation outside the block is needed, because ``user`` is already the unwrapped ``dict`` value at that point.

Step 3: When the final function returns a monad, just yield it
--------------------------------------------------------------

If a step itself returns a ``Maybe`` (or whichever monad you are working with), pass its result straight to ``yield``. No special ``eval`` call is needed - ``yield`` handles both plain-returning and monad-returning steps the same way:

.. code-block:: python

   def budget_report_safe(user: dict, team: dict) -> Maybe[str]:
       if team["budget"] < 0:
           return Maybe[str].Nothing()
       return Maybe[str].Just(f"{user['name']} - budget: {team['budget']}")

   @do(Maybe)
   def block() -> DoBlock[Maybe, str]:
       user:   dict = yield find_user(1)
       team:   dict = yield find_team(user["team_id"])
       report: str  = yield budget_report_safe(user, team)  # returns Maybe - just yield it
       return report

   result = block()

Step 4: Verify the result is identical
----------------------------------------

Run both versions side by side to confirm they produce the same value:

.. code-block:: python

   assert result_bind == result
