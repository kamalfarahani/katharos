Do Syntax: Cleaner Monadic Code
=================================

In this tutorial, you'll learn how to use do syntax to write cleaner, more readable monadic code without deeply nested lambdas.

What You'll Learn
-----------------

- Why nested bind operations become hard to read
- How do syntax simplifies monadic code
- How to use ``Do`` context manager
- How to extract values with ``arrow``
- How to return values with ``ret``

Prerequisites
-------------

Complete the :doc:`first-monad` tutorial first to understand bind operations and monadic chains.

The Problem: Nested Lambdas
----------------------------

When chaining multiple monadic operations that depend on previous results, the code quickly becomes nested and hard to read:

.. code-block:: python

   from katharos.types import Maybe

   def get_input() -> Maybe[float]:
       """Get a float from user input."""
       try:
           x = float(input("Enter number: "))
           return Maybe.Just(x)
       except Exception:
           return Maybe.Nothing()

   def process(x: float, y: float, z: float) -> float:
       """Process three numbers."""
       return x * 2 + y + z**2

   # Using bind - gets messy quickly!
   m_x1 = get_input()
   m_x2 = get_input()
   m_x3 = get_input()

   result = m_x1 | (
       lambda x1: (
           m_x2 | (lambda x2: m_x3 | (lambda x3: Maybe.ret(process(x1, x2, x3))))
       )
   )
   print(result)

Notice how:

- The code is deeply nested with multiple lambdas
- It's hard to see the flow of data
- Each lambda captures variables from outer scopes
- Adding more steps makes it exponentially harder to read

The Solution: Do Syntax
------------------------

Do syntax provides a cleaner way to write the same logic:

.. code-block:: python

   from katharos.syntax_sugar import Do
   from katharos.types import Maybe

   # Same functions as before
   def get_input() -> Maybe[float]:
       try:
           x = float(input("Enter number: "))
           return Maybe.Just(x)
       except Exception:
           return Maybe.Nothing()

   def process(x: float, y: float, z: float) -> float:
       return x * 2 + y + z**2

   # Using do syntax - much cleaner!
   with Do[Maybe]() as do:
       x1_var = do.arrow(get_input())
       x2_var = do.arrow(get_input())
       x3_var = do.arrow(get_input())
       result = do.ret(
           process,
           x=x1_var,
           y=x2_var,
           z=x3_var,
       )

   print(result)

This is much more readable:

- ✅ No nested lambdas
- ✅ Linear, imperative-style flow
- ✅ Clear variable names
- ✅ Easy to add or remove steps

How Do Syntax Works
--------------------

The ``Do`` context manager provides two key methods:

``do.arrow(monadic_value)``
  Extracts the value from a monad. Returns a placeholder that represents the unwrapped value.

``do.ret(function, **kwargs)``
  Applies a function to extracted values and wraps the result back in the monad.

Behind the scenes, do syntax translates your code into the nested bind operations, but you don't have to write them manually!

Step-by-Step Example
---------------------

Let's build a user profile system to see do syntax in action:

.. code-block:: python

   from katharos.syntax_sugar import Do
   from katharos.types import Maybe

   # Simulated database
   users = {
       1: {"name": "Alice", "age": 30, "city_id": 101},
       2: {"name": "Bob", "age": 25, "city_id": 102},
   }

   cities = {
       101: {"name": "New York", "country_id": 1},
       102: {"name": "London", "country_id": 2},
   }

   countries = {
       1: {"name": "USA", "currency": "USD"},
       2: {"name": "UK", "currency": "GBP"},
   }

   def get_user(user_id: int) -> Maybe[dict]:
       user = users.get(user_id)
       return Maybe.Just(user) if user else Maybe.Nothing()

   def get_city(city_id: int) -> Maybe[dict]:
       city = cities.get(city_id)
       return Maybe.Just(city) if city else Maybe.Nothing()

   def get_country(country_id: int) -> Maybe[dict]:
       country = countries.get(country_id)
       return Maybe.Just(country) if country else Maybe.Nothing()

   def format_profile(user_name: str, city_name: str, currency: str) -> str:
       return f"{user_name} lives in {city_name} and uses {currency}"

Without Do Syntax
~~~~~~~~~~~~~~~~~

First, let's see how this looks with nested bind operations:

.. code-block:: python

   # Nested and hard to follow
   result = get_user(1) | (
       lambda user: get_city(user["city_id"]) | (
           lambda city: get_country(city["country_id"]) | (
               lambda country: Maybe.ret(
                   format_profile(
                       user["name"],
                       city["name"],
                       country["currency"]
                   )
               )
           )
       )
   )
   print(result)  # Just('Alice lives in New York and uses USD')

With Do Syntax
~~~~~~~~~~~~~~

Now with do syntax - much cleaner:

.. code-block:: python

   # Clean and readable
   with Do[Maybe]() as do:
       user = do.arrow(get_user(1))
       city = do.arrow(get_city(user["city_id"]))
       country = do.arrow(get_country(city["country_id"]))
       result = do.ret(
           format_profile,
           user_name=user["name"],
           city_name=city["name"],
           currency=country["currency"],
       )

   print(result)  # Just('Alice lives in New York and uses USD')

The benefits are clear:

- Each step is on its own line
- Variable names make the data flow obvious
- Easy to debug - you can see exactly which step might fail
- Adding new steps is trivial

Working with Multiple Monads
-----------------------------

Do syntax works with any monad type. Here's an example with ``Result``:

.. code-block:: python

   from katharos.syntax_sugar import Do
   from katharos.types import Result

   def safe_divide(a: float, b: float) -> Result[Exception, float]:
       if b == 0:
           return Result.Failure(ZeroDivisionError("Division by zero"))
       return Result.Success(a / b)

   def safe_sqrt(x: float) -> Result[Exception, float]:
       if x < 0:
           return Result.Failure(ValueError("Cannot take square root of negative number"))
       return Result.Success(x ** 0.5)

   def safe_log(x: float) -> Result[Exception, float]:
       if x <= 0:
           return Result.Failure(ValueError("Cannot take log of non-positive number"))
       import math
       return Result.Success(math.log(x))

   # Without do syntax
   result_nested = safe_divide(100, 4) | (
       lambda x: safe_sqrt(x) | (
           lambda y: safe_log(y) | (
               lambda z: Result.ret(z * 10)
           )
       )
   )

   # With do syntax
   with Do[Result]() as do:
       x = do.arrow(safe_divide(100, 4))  # 25
       y = do.arrow(safe_sqrt(x))          # 5
       z = do.arrow(safe_log(y))           # ~1.609
       result = do.ret(lambda val: val * 10, val=z)

   print(result)  # Success(16.09...)

Complex Example: Data Pipeline
-------------------------------

Let's build a more complex example that processes user data through multiple validation and transformation steps:

.. code-block:: python

   from katharos.syntax_sugar import Do
   from katharos.types import Result

   def validate_age(age: int) -> Result[Exception, int]:
       if age < 0 or age > 150:
           return Result.Failure(ValueError(f"Invalid age: {age}"))
       return Result.Success(age)

   def validate_email(email: str) -> Result[Exception, str]:
       if "@" not in email:
           return Result.Failure(ValueError(f"Invalid email: {email}"))
       return Result.Success(email)

   def calculate_discount(age: int) -> float:
       if age < 18:
           return 0.0
       elif age < 65:
           return 0.1
       else:
           return 0.2

   def format_welcome(email: str, age: int, discount: float) -> str:
       return f"Welcome {email}! Age: {age}, Discount: {discount*100}%"

   # Without do syntax - deeply nested
   def process_user_nested(email: str, age: int) -> Result[Exception, str]:
       return validate_email(email) | (
           lambda valid_email: validate_age(age) | (
               lambda valid_age: Result.ret(
                   format_welcome(
                       valid_email,
                       valid_age,
                       calculate_discount(valid_age)
                   )
               )
           )
       )

   # With do syntax - clear and linear
   def process_user_clean(email: str, age: int) -> Result[Exception, str]:
       with Do[Result]() as do:
           valid_email = do.arrow(validate_email(email))
           valid_age = do.arrow(validate_age(age))
           discount = calculate_discount(valid_age)
           result = do.ret(
               format_welcome,
               email=valid_email,
               age=valid_age,
               discount=discount,
           )
       return result

   # Test it
   print(process_user_clean("alice@example.com", 30))
   # Success('Welcome alice@example.com! Age: 30, Discount: 10.0%')

   print(process_user_clean("invalid-email", 30))
   # Failure(ValueError('Invalid email: invalid-email'))

   print(process_user_clean("bob@example.com", 200))
   # Failure(ValueError('Invalid age: 200'))

Notice how the do syntax version:

- Clearly separates validation from calculation
- Makes it obvious which values are monadic (extracted with ``arrow``) vs pure (like ``discount``)
- Is easy to extend with new validation or transformation steps
- Reads like imperative code but maintains all the safety of monadic composition

When to Use Do Syntax
----------------------

Use do syntax when:

- ✅ You have multiple monadic operations that depend on each other
- ✅ You need to use values from earlier steps in later steps
- ✅ Readability is important (almost always!)
- ✅ You're working with 3+ chained operations

Stick with bind (``|``) when:

- You have a simple 1-2 step chain
- The operations don't depend on each other's values
- You're writing point-free style code

Comparison Summary
------------------

Here's a side-by-side comparison:

.. code-block:: python

   # Bind style - good for simple chains
   result = get_user(1) | get_manager_id | get_user

   # Do style - better for complex logic
   with Do[Maybe]() as do:
       user = do.arrow(get_user(1))
       manager_id = do.arrow(get_manager_id(user))
       manager = do.arrow(get_user(manager_id))
       result = do.ret(lambda m: m, m=manager)

What You've Learned
-------------------

Congratulations! You now understand:

- ✅ Why nested bind operations become unreadable
- ✅ How do syntax provides a cleaner alternative
- ✅ How to use ``Do`` context manager with ``arrow`` and ``ret``
- ✅ When to use do syntax vs bind operations
- ✅ How to work with different monad types using do syntax

Next Steps
----------

- Learn about :doc:`error-handling` to use do syntax with ``Result``
- Explore :doc:`../how-to/chain-operations` for advanced patterns
- Read :doc:`../explanation/monad-laws` to understand the theory

Further Reading
---------------

- :class:`katharos.syntax_sugar.Do` - API reference
- :doc:`../explanation/do-notation` - Theory behind do notation
- :doc:`../how-to/refactor-to-do` - Refactoring guide
