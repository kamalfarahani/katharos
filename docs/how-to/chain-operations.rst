How to Chain Monadic Operations
================================

This guide shows you how to chain ``Maybe`` and ``Result`` operations using the ``|`` bind operator so that each step in a pipeline receives the unwrapped value from the previous step and the chain short-circuits automatically on failure.

Prerequisites
-------------

- Familiarity with ``Maybe.Just`` / ``Maybe.Nothing`` and ``Result.Success`` / ``Result.Failure``

Chaining with Maybe
--------------------

Use ``|`` to pass the unwrapped value of a ``Just`` into the next function. If any step returns ``Nothing()``, all subsequent steps are skipped.

.. code-block:: python

   from katharos.types import Maybe

   def lookup_user(uid: int) -> Maybe[dict]:
       users = {1: {"name": "Alice", "role_id": 3}, 2: {"name": "Bob"}}
       u = users.get(uid)
       return Maybe[dict].Just(u) if u is not None else Maybe[dict].Nothing()

   def lookup_role(user: dict) -> Maybe[str]:
       roles = {3: "admin", 4: "viewer"}
       role_id = user.get("role_id")
       if role_id is None:
           return Maybe[str].Nothing()
       r = roles.get(role_id)
       return Maybe[str].Just(r) if r is not None else Maybe[str].Nothing()

   def format_badge(role: str) -> Maybe[str]:
       return Maybe[str].Just(f"[{role.upper()}]")

   result = (
       lookup_user(1)
       | lookup_role
       | format_badge
   )
   # result == Just('[ADMIN]')

   missing = (
       lookup_user(2)
       | lookup_role      # returns Nothing() - Bob has no role_id
       | format_badge     # skipped
   )
   # missing == Nothing()

Chaining with Result
---------------------

``Result`` follows the same pattern. A ``Failure`` short-circuits the chain and carries the original exception through to the end.

.. code-block:: python

   import json
   from katharos.types import Result

   def read_file(path: str) -> Result[Exception, str]:
       try:
           with open(path) as f:
               return Result[Exception, str].Success(f.read())
       except OSError as e:
           return Result[Exception, str].Failure(e)

   def parse_json(text: str) -> Result[Exception, dict]:
       try:
           return Result[Exception, dict].Success(json.loads(text))
       except json.JSONDecodeError as e:
           return Result[Exception, dict].Failure(e)

   def get_host(config: dict) -> Result[Exception, str]:
       host = config.get("host")
       if host is None:
           return Result[Exception, str].Failure(KeyError("missing 'host' key"))
       return Result[Exception, str].Success(host)

   result = (
       read_file("config.json")
       | parse_json
       | get_host
   )
   # result == Success('localhost')

   bad = (
       read_file("missing.json")   # Failure(FileNotFoundError(...))
       | parse_json                # skipped
       | get_host                  # skipped
   )
   # bad == Failure(FileNotFoundError(...))

Accessing the final value
--------------------------

Call ``.unwrap()`` on a ``Just`` or ``Success`` to get the inner value when you are ready to leave the functional pipeline:

.. code-block:: python

   value = result.unwrap()  # 'localhost'

Check the state before unwrapping when the result may be a failure:

.. code-block:: python

   if result.is_success():
       print(result.unwrap())
   else:
       print(f"Error: {result.error}")

Mixing ``fmap`` and ``|``
--------------------------

Use ``fmap`` for infallible steps (the transform always produces a value); use ``|`` for steps that may return ``Nothing`` or ``Failure``.

.. code-block:: python

   result = (
       read_file("config.json")
       | parse_json                              # fallible - use |
       .fmap(lambda cfg: cfg.get("host", "localhost"))  # infallible - use fmap
       | get_host                                # fallible - use |
   )
