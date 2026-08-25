How to Handle Errors Without Exceptions
========================================

This guide covers practical patterns for using ``Result`` and ``Maybe`` to represent and propagate errors without raising exceptions - including wrapping existing exception-throwing code, recovering from failures, and converting between the two types.

Prerequisites
-------------

- Familiarity with ``Result.Success`` / ``Result.Failure`` and the ``|`` operator
- Familiarity with ``Maybe.Just`` / ``Maybe.Nothing``

Wrapping code that raises exceptions
--------------------------------------

Convert an exception-throwing call into a ``Result`` using a try/except at the boundary:

.. code-block:: python

   from katharos.types import Result

   def read_file(path: str) -> Result[Exception, str]:
       try:
           with open(path) as f:
               return Result.Success(f.read())
       except OSError as e:
           return Result.Failure(e)

   def parse_json(text: str) -> Result[Exception, dict]:
       import json
       try:
           return Result.Success(json.loads(text))
       except json.JSONDecodeError as e:
           return Result.Failure(e)

Chain these with ``|`` - a failure at any step short-circuits the rest:

.. code-block:: python

   config = (
       read_file("config.json")
       | parse_json
   )

   if config.is_success():
       print(config.value)
   else:
       print(f"Could not load config: {config.error}")

Converting a None-returning function to Maybe
----------------------------------------------

Wrap a call that returns ``None`` on absence with ``Maybe``:

.. code-block:: python

   from katharos.types import Maybe

   def find_user(uid: int) -> Maybe[dict]:
       db = {1: {"name": "Alice"}, 2: {"name": "Bob"}}
       user = db.get(uid)          # returns None when absent
       return Maybe.Just(user) if user is not None else Maybe.Nothing()

Providing a default value on Nothing
--------------------------------------

Use a conditional after the pipeline to supply a fallback:

.. code-block:: python

   user = find_user(99)
   name = user.fmap(lambda u: u["name"])

   display = name.unwrap() if name.is_just() else "Guest"
   print(display)  # Guest

Recovering from a Failure
--------------------------

To attempt a fallback when a ``Result`` fails, branch on ``.is_failure()``:

.. code-block:: python

   def read_file_or_default(path: str, default: str) -> str:
       result = read_file(path)
       if result.is_failure():
           return default
       return result.value

For a monadic fallback - where the recovery itself may also fail - use a plain conditional rather than chaining ``|``, since ``|`` only runs when the preceding step succeeded:

.. code-block:: python

   def load_config(primary: str, fallback: str) -> Result[Exception, dict]:
       result = read_file(primary) | parse_json
       if result.is_failure():
           return read_file(fallback) | parse_json
       return result

Using do-notation to flatten multi-step pipelines
---------------------------------------------------

When several ``Result``-returning steps depend on one another, the ``@do`` decorator
lets you write them as a plain sequence of bindings instead of a ``|`` chain.
Each ``yield`` unwraps the value on success; the first ``Failure`` short-circuits
the entire block and is returned immediately - no subsequent steps run.

Rewriting the config pipeline with do-notation:

.. code-block:: python

   from katharos.syntax_sugar import do, DoBlock
   from katharos.types import Result

   @do(Result)
   def load_config(path: str) -> DoBlock[Result, dict]:
       text:   str  = yield read_file(path)
       config: dict = yield parse_json(text)
       return config

   result = load_config("config.json")

   if result.is_success():
       print(result.value)
   else:
       print(f"Could not load config: {result.error}")

If ``read_file`` returns a ``Failure``, the block stops there and ``parse_json`` is
never called.  If ``parse_json`` fails, that ``Failure`` is what the block returns.

Do-notation is especially readable when intermediate values need to be used in later
steps:

.. code-block:: python

   def get_setting(config: dict, key: str) -> Result[Exception, str]:
       if key not in config:
           return Result.Failure(KeyError(f"missing key: {key!r}"))
       return Result.Success(config[key])

   @do(Result)
   def load_host_and_port(path: str) -> DoBlock[Result, tuple[str, str]]:
       text:   str  = yield read_file(path)
       config: dict = yield parse_json(text)
       host:   str  = yield get_setting(config, "host")
       port:   str  = yield get_setting(config, "port")
       return host, port

   load_host_and_port("config.json")
   # Success(('localhost', '8080'))  - or Failure at whichever step first fails

Converting between Maybe and Result
--------------------------------------

Convert ``Maybe`` to ``Result`` when you need to attach an error message to an absence:

.. code-block:: python

   def maybe_to_result(m: Maybe[dict], uid: int) -> Result[Exception, dict]:
       if m.is_just():
           return Result.Success(m.unwrap())
       return Result.Failure(KeyError(f"User {uid} not found"))

   user_result = maybe_to_result(find_user(42), 42)

Convert ``Result`` to ``Maybe`` when you want to discard the error and treat failure as absence:

.. code-block:: python

   def result_to_maybe(r: Result) -> Maybe:
       if r.is_success():
           return Maybe.Just(r.value)
       return Maybe.Nothing()

Accumulating multiple independent errors
-----------------------------------------

When validating several independent fields and you want all failures at once (not just the first), collect them explicitly before constructing a ``Result``:

.. code-block:: python

   def validate_name(name: str) -> Result[Exception, str]:
       if not name.strip():
           return Result.Failure(ValueError("name cannot be blank"))
       return Result.Success(name.strip())

   def validate_age(age: int) -> Result[Exception, int]:
       if age < 0 or age > 150:
           return Result.Failure(ValueError(f"age {age} is out of range"))
       return Result.Success(age)

   def validate_user(name: str, age: int) -> Result[Exception, dict]:
       name_result = validate_name(name)
       age_result  = validate_age(age)

       errors = [
           r.error for r in [name_result, age_result] if r.is_failure()
       ]

       if errors:
           combined = ValueError("; ".join(str(e) for e in errors))
           return Result.Failure(combined)

       return Result.Success({"name": name_result.value, "age": age_result.value})

   print(validate_user("", -5))
   # Failure(ValueError('name cannot be blank; age -5 is out of range'))
