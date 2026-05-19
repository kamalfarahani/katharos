Error Handling with Result
==========================

Learn how to handle errors functionally using the ``Result`` type, eliminating exceptions and making error handling explicit.

What You'll Learn
-----------------

- How to use ``Result`` for error handling
- The difference between ``Result`` and ``Maybe``
- How to chain operations that can fail
- Best practices for functional error handling

The Problem with Exceptions
----------------------------

Traditional exception-based error handling has issues:

.. code-block:: python

   def divide(a: float, b: float) -> float:
       if b == 0:
           raise ZeroDivisionError("Cannot divide by zero")
       return a / b
   
   # Caller must remember to catch exceptions
   try:
       result = divide(10, 0)
   except ZeroDivisionError as e:
       print(f"Error: {e}")

**Problems:**

- Exceptions are invisible in type signatures
- Easy to forget error handling
- Breaks referential transparency
- Makes control flow implicit

Introducing Result
------------------

``Result`` makes errors explicit in the type system:

.. code-block:: python

   from katharos.types import Result
   
   def safe_divide(a: float, b: float) -> Result[Exception, float]:
       if b == 0:
           return Result[Exception, float].Failure(ZeroDivisionError("Cannot divide by zero"))
       return Result[Exception, float].Success(a / b)
   
   # Type tells you this can fail!
   result = safe_divide(10, 2)
   print(result)  # Success(5.0)
   
   result = safe_divide(10, 0)
   print(result)  # Failure(ZeroDivisionError('Cannot divide by zero'))

Creating Results
----------------

Success Values
~~~~~~~~~~~~~~

.. code-block:: python

   from katharos.types import Result
   
   success = Result[Exception, int].Success(42)
   print(success)  # Success(42)
   print(success.is_success())  # True
   print(success.value)  # 42

Failure Values
~~~~~~~~~~~~~~

.. code-block:: python

   from katharos.types import Result
   
   failure = Result[ValueError, int].Failure(ValueError("Invalid input"))
   print(failure)  # Failure(ValueError('Invalid input'))
   print(failure.is_failure())  # True
   print(failure.error)  # ValueError('Invalid input')

Mapping Over Results
--------------------

Use ``fmap`` to transform success values:

.. code-block:: python

   from katharos.types import Result
   
   # Success case
   result = Result[Exception, int].Success(5).fmap(lambda x: x * 2)
   print(result)  # Success(10)
   
   # Failure case - function never called
   result = Result[ValueError, int].Failure(ValueError("error")).fmap(lambda x: x * 2)
   print(result)  # Failure(ValueError('error'))

Chaining Operations
-------------------

Use bind (``|``) to chain operations that return ``Result``:

.. code-block:: python

   from katharos.types import Result
   
   def safe_divide(a: float, b: float) -> Result[Exception, float]:
       if b == 0:
           return Result[Exception, float].Failure(ZeroDivisionError("Cannot divide by zero"))
       return Result[Exception, float].Success(a / b)
   
   def safe_sqrt(x: float) -> Result[Exception, float]:
       if x < 0:
           return Result[Exception, float].Failure(ValueError("Negative square root"))
       return Result[Exception, float].Success(x ** 0.5)
   
   # Chain operations
   result = (
       safe_divide(16, 4)      # Success(4.0)
       | safe_sqrt             # Success(2.0)
   )
   print(result)  # Success(2.0)
   
   # Fails at first error
   result = (
       safe_divide(16, 0)      # Failure!
       | safe_sqrt             # Never executed
   )
   print(result)  # Failure(ZeroDivisionError('Cannot divide by zero'))

When to Use ``fmap`` vs Bind
----------------------------

Both ``fmap`` and bind (``|``) let you transform the value inside a ``Result``,
but they handle different shapes of function:

- Use ``fmap`` when your function returns a **plain value** (``A -> B``).
- Use bind (``|``) when your function itself returns a ``Result`` (``A -> Result[E, B]``).

If you used ``fmap`` with a ``Result``-returning function you'd end up with a
nested ``Result[E, Result[E, B]]``. Bind flattens that for you.

.. code-block:: python

   # fmap: function returns a plain int
   Result[Exception, int].Success(5).fmap(lambda x: x + 1)
   # Success(6)

   # bind: function returns a Result
   def half(x: int) -> Result[Exception, float]:
       if x == 0:
           return Result[Exception, float].Failure(ZeroDivisionError("zero"))
       return Result[Exception, float].Success(x / 2)

   Result[Exception, int].Success(10) | half
   # Success(5.0)

Practical Example: Input Validation
------------------------------------

The ``Do`` helper provides do-notation: a sequential, imperative-looking syntax
for chaining monadic operations. Each ``do.arrow(...)`` call extracts the value
from a ``Result`` (short-circuiting on ``Failure``), and ``do.ret(...)`` wraps
the final result back into the monad. It's equivalent to a chain of binds, just
easier to read when you have several dependent steps.

.. code-block:: python

    from katharos.syntax_sugar import Do
    from katharos.types import Result


    def validate_age(age: int) -> Result[Exception, int]:
        if age < 0:
            return Result[Exception, int].Failure(ValueError("Age cannot be negative"))
        if age > 150:
            return Result[Exception, int].Failure(ValueError("Age too high"))
        return Result[Exception, int].Success(age)


    def validate_name(name: str) -> Result[Exception, str]:
        if not name:
            return Result[Exception, str].Failure(ValueError("Name cannot be empty"))
        if len(name) < 2:
            return Result[Exception, str].Failure(ValueError("Name too short"))
        return Result[Exception, str].Success(name)


    def create_user(name: str, age: int) -> Result[Exception, dict]:
        with Do[Result]() as do:
            name_var = do.arrow(validate_name(name))
            age_var = do.arrow(validate_age(age))
            result = do.ret(
                lambda n, a: {"name": n, "age": a},
                n=name_var,
                a=age_var,
            )
        return result


    # Valid input
    user = create_user("Alice", 30)
    print(user)  # Success({'name': 'Alice', 'age': 30})

    # Invalid input
    user = create_user("A", 30)
    print(user)  # Failure(ValueError('Name too short'))

    user = create_user("Alice", -5)
    print(user)  # Failure(ValueError('Age cannot be negative'))

Result vs Maybe
---------------

When to Use Result
~~~~~~~~~~~~~~~~~~

Use ``Result`` when you need to know **why** something failed:

.. code-block:: python

   from katharos.types import Result
   
   def parse_int(s: str) -> Result[Exception, int]:
       try:
           return Result[Exception, int].Success(int(s))
       except ValueError as e:
           return Result[Exception, int].Failure(e)  # Preserve error info
   
   result = parse_int("not a number")
   if result.is_failure():
       print(f"Error: {result.error}")  # Error: invalid literal...

When to Use Maybe
~~~~~~~~~~~~~~~~~

Use ``Maybe`` when failure is expected and you don't need error details:

.. code-block:: python

   from katharos.types import Maybe
   
   # Pseudo-code: assume `database` is some dict-like store.
   def find_user(user_id: int) -> Maybe[dict]:
       user = database.get(user_id)
       return Maybe[dict].Nothing() if user is None else Maybe[dict].Just(user)

**Rule of thumb:**

- ``Result`` = "This might fail, here's why"
- ``Maybe`` = "This might be absent"

Converting Between Result and Maybe
------------------------------------

Result to Maybe
~~~~~~~~~~~~~~~

.. code-block:: python

   from katharos.types import Result, Maybe
   
   def result_to_maybe[E: Exception, T](result: Result[E, T]) -> Maybe[T]:
       if result.is_success():
           return Maybe.Just(result.value)
       return Maybe.Nothing()
   
   success = Result[Exception, int].Success(42)
   print(result_to_maybe(success))  # Just(42)
   
   failure = Result[ValueError, int].Failure(ValueError("error"))
   print(result_to_maybe(failure))  # Nothing()

Maybe to Result
~~~~~~~~~~~~~~~

.. code-block:: python

   from katharos.types import Result, Maybe
   
   def maybe_to_result[E: Exception, T](
       maybe: Maybe[T], error: E
   ) -> Result[E, T]:
       if maybe.is_just():
           return Result.Success(maybe.unwrap())
       return Result.Failure(error)
   
   just = Maybe[int].Just(42)
   print(maybe_to_result(just, ValueError("missing")))  # Success(42)
   
   nothing = Maybe[int].Nothing()
   print(maybe_to_result(nothing, ValueError("missing")))
   # Failure(ValueError('missing'))

Best Practices
--------------

1. **Make errors specific in the type signature**

   Prefer narrow error types so the signature documents *what* can go wrong.
   ``Result[Exception, T]`` is opaque — it tells the caller "something can
   fail" but not what.

   .. code-block:: python
   
      # Good - specific error type, encoded in the signature
      def validate_age(age: int) -> Result[ValueError, int]:
          if not 0 <= age <= 150:
              return Result[ValueError, int].Failure(
                  ValueError("Age must be between 0 and 150")
              )
          return Result[ValueError, int].Success(age)

      # Bad - opaque error type, callers can't tell what failures to expect
      def validate_age(age: int) -> Result[Exception, int]:
          ...

2. **Use custom exception types**

   .. code-block:: python
   
      class ValidationError(Exception):
          pass
      
      def validate(x: int) -> Result[ValidationError, int]:
          if x < 0:
              return Result[ValidationError, int].Failure(ValidationError("Negative value"))
          return Result[ValidationError, int].Success(x)

3. **Document error cases**

   .. code-block:: python
   
      def parse_config(path: str) -> Result[Exception, dict]:
          """Parse configuration file.
          
          Returns:
              Success with config dict, or Failure with:
              - FileNotFoundError if file doesn't exist
              - JSONDecodeError if file is invalid JSON
              - PermissionError if file can't be read
          """
          ...

4. **Keep error handling at boundaries**

   Use ``Result`` internally, convert to exceptions at API boundaries if needed:
   
   .. code-block:: python
   
      def public_api(x: int) -> int:
          """Public API that raises exceptions."""
          result = internal_logic(x)
          if result.is_failure():
              raise result.error
          return result.value
      
      def internal_logic(x: int) -> Result[Exception, int]:
          """Internal logic using Result."""
          ...

What You've Learned
-------------------

- ✅ How to create ``Success`` and ``Failure`` values
- ✅ How to map and chain ``Result`` operations
- ✅ When to use ``Result`` vs ``Maybe``
- ✅ How to convert between ``Result`` and ``Maybe``
- ✅ Best practices for functional error handling

Next Steps
----------

- Learn about :doc:`../how-to/error-handling` for advanced patterns
- Explore :doc:`immutable-lists` for working with collections
- Read :doc:`../explanation/fp-concepts` for deeper understanding

See Also
--------

- :class:`katharos.types.Result` - API reference
- :class:`katharos.types.Maybe` - Alternative for optional values
- :doc:`../how-to/chain-operations` - Chaining patterns
