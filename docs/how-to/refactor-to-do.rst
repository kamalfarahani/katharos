How to Refactor Bind Chains to Do-Notation
==========================================

This guide shows you how to convert a nested bind chain — with multiple lambdas capturing outer values — into equivalent do-notation that is easier to read and modify.

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

Do not refactor if you have a simple linear chain where each step does not capture a previous result — the ``|`` form is already concise there.

Step 1: Identify the nested capture pattern
--------------------------------------------

This is the signal: a lambda inside a lambda captures an outer variable.

.. code-block:: python

   from katharos.types import Maybe

   def find_user(uid: int) -> Maybe[dict]:
       users = {1: {"name": "Alice", "team_id": 10}}
       return Maybe.Just(users[uid]) if uid in users else Maybe.Nothing()

   def find_team(tid: int) -> Maybe[dict]:
       teams = {10: {"name": "Engineering", "budget": 50_000}}
       return Maybe.Just(teams[tid]) if tid in teams else Maybe.Nothing()

   def budget_report(user: dict, team: dict) -> str:
       return f"{user['name']} is in {team['name']} with budget {team['budget']}"

   # Before: nested lambda captures `user` from outer scope
   result = (
       find_user(1)
       | (lambda user:
           find_team(user["team_id"])
           | (lambda team:
               Maybe.Just(budget_report(user, team))
           )
       )
   )

The inner lambda captures ``user`` from the outer lambda. This nesting grows with every additional value you need.

Step 2: Replace with Do[M]
---------------------------

Each ``lambda x: ...`` in the bind chain maps directly to a ``do.arrow`` call:

.. code-block:: python

   from katharos.syntax_sugar import Do

   with Do[Maybe]() as do:
       user   = do.arrow(find_user(1))
       team   = do.arrow(find_team(user["team_id"]))  # note: user is still a placeholder here
       result = do.ret(budget_report, user=user, team=team)

.. warning::

   ``user`` returned by ``do.arrow`` is a ``DoVariable`` placeholder, not the actual unwrapped dict. Do not call methods on it or pass it to non-do-block code between ``do.arrow`` and ``do.ret``/``do.eval``. Only pass it as a keyword argument to ``do.ret`` or ``do.eval``.

   The expression ``find_team(user["team_id"])`` in the example above works because ``do.arrow`` is called with the *full expression* as the argument — the expression is evaluated immediately. You cannot write ``user_id = user["team_id"]`` outside of a ``do.ret``/``do.eval`` call.

   Instead, compute derived inputs inside the ``do.arrow`` call:

   .. code-block:: python

      with Do[Maybe]() as do:
          user    = do.arrow(find_user(1))
          team_id = do.arrow(find_user(1).fmap(lambda u: u["team_id"]))  # extract first
          team    = do.arrow(...)

   Or restructure the functions so each step takes a single value.

Step 3: Use do.eval when the final function returns a monad
-----------------------------------------------------------

If ``budget_report`` itself returned a ``Maybe[str]`` instead of a plain ``str``, switch from ``do.ret`` to ``do.eval``:

.. code-block:: python

   def budget_report_safe(user: dict, team: dict) -> Maybe[str]:
       if team["budget"] < 0:
           return Maybe.Nothing()
       return Maybe.Just(f"{user['name']} — budget: {team['budget']}")

   with Do[Maybe]() as do:
       user   = do.arrow(find_user(1))
       team   = do.arrow(find_team(user["team_id"]))
       result = do.eval(budget_report_safe, user=user, team=team)

Step 4: Verify the result is identical
----------------------------------------

Run both versions side by side to confirm they produce the same value:

.. code-block:: python

   assert result_bind == result_do
