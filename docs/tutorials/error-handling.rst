Build a User Registration System with Result
============================================

In this tutorial, we will build a user registration system that handles errors functionally. Along the way, we will encounter ``Result``, ``fmap``, the ``|`` operator for chaining validations, and the ``@do`` decorator for combining multiple results cleanly.

.. note::

   Always supply both type arguments when constructing a ``Result`` value — use ``Result[Exception, str].Success("ok")`` and ``Result[Exception, str].Failure(err)``, not ``Result.Success("ok")``. The two type parameters are the error type and the success type; providing them lets your type checker verify each step of the pipeline.

Prerequisites
-------------

- Python 3.13 or later
- Katharos installed (see :doc:`getting-started`)
- Complete the :doc:`handling-null` tutorial so you are familiar with ``Maybe``

Step 1: Create Your First Result
---------------------------------

Create a new Python file called ``registration.py`` with the following contents:

.. code-block:: python

   from katharos.types import Result

   def check_password_length(password: str) -> Result[Exception, str]:
       if len(password) >= 8:
           return Result[Exception, str].Success(password)
       return Result[Exception, str].Failure(ValueError("Password too short"))

   print(check_password_length("secret123"))
   print(check_password_length("short"))

Run the file:

.. code-block:: bash

   python registration.py

You should see:

.. code-block:: text

   Success(secret123)
   Failure(ValueError('Password too short'))

Notice how the ``Result`` wraps a valid password in ``Success`` and captures an error in ``Failure`` — no exception is raised.

Step 2: Add Email Validation
-----------------------------

Now we will add another validation function. Remove the two ``print`` lines from the bottom of ``registration.py`` and add:

.. code-block:: python

   def check_email_format(email: str) -> Result[Exception, str]:
       if "@" in email and "." in email:
           return Result[Exception, str].Success(email)
       return Result[Exception, str].Failure(ValueError("Invalid email format"))

   print(check_email_format("user@example.com"))
   print(check_email_format("notanemail"))

Run the file:

.. code-block:: bash

   python registration.py

You should see:

.. code-block:: text

   Success(user@example.com)
   Failure(ValueError('Invalid email format'))

Step 3: Transform a Success Value with fmap
--------------------------------------------

We will now normalise the email to lowercase using ``fmap``. Replace the two ``print`` lines with:

.. code-block:: python

   print(check_email_format("User@Example.COM").fmap(lambda email: email.lower()))
   print(check_email_format("invalid").fmap(lambda email: email.lower()))

Run the file:

.. code-block:: bash

   python registration.py

You should see:

.. code-block:: text

   Success(user@example.com)
   Failure(ValueError('Invalid email format'))

Notice that ``fmap`` applied the lowercase transformation only to the ``Success`` value. The ``Failure`` passed through unchanged without ever calling the lambda.

Step 4: Chain Validations with |
----------------------------------

Now we will chain multiple validations using the ``|`` operator. Remove the two ``print`` lines and add:

.. code-block:: python

   def check_password_strength(password: str) -> Result[Exception, str]:
       if any(c.isdigit() for c in password):
           return Result[Exception, str].Success(password)
       return Result[Exception, str].Failure(ValueError("Password must contain a number"))

   print(check_password_length("secret123") | check_password_strength)
   print(check_password_length("secretword") | check_password_strength)
   print(check_password_length("short") | check_password_strength)

Run the file:

.. code-block:: bash

   python registration.py

You should see:

.. code-block:: text

   Success(secret123)
   Failure(ValueError('Password must contain a number'))
   Failure(ValueError('Password too short'))

Notice how the chain stops at the first ``Failure``. In the third case, ``check_password_strength`` is never called because the password was already rejected by ``check_password_length``.

Step 5: Build the Registration Function
----------------------------------------

Now we will combine everything into a single registration function using the ``@do`` decorator. Remove the three ``print`` lines and add:

.. code-block:: python

   from katharos.syntax_sugar import do, DoBlock

   def register_user(email: str, password: str) -> Result[Exception, dict]:
       @do(Result)
       def block() -> DoBlock[Result, dict]:
           validated_email: str = yield check_email_format(email).fmap(lambda e: e.lower())
           validated_password: str = yield check_password_length(password) | check_password_strength
           return {"email": validated_email, "password": validated_password}

       return block()

   print(register_user("Alice@Example.com", "secret123"))
   print(register_user("notanemail", "secret123"))
   print(register_user("alice@example.com", "short"))

Run the file:

.. code-block:: bash

   python registration.py

You should see:

.. code-block:: text

   Success({'email': 'alice@example.com', 'password': 'secret123'})
   Failure(ValueError('Invalid email format'))
   Failure(ValueError('Password too short'))

Notice that the block stops at the first ``Failure`` and returns it immediately, without running the remaining ``yield`` steps. Also notice that ``validated_email`` and ``validated_password`` are real ``str`` values inside the block — they can be used directly in the ``return`` expression without any placeholder workaround.

Step 6: Extract Values from Results
------------------------------------

Now we will extract the user data when registration succeeds. Replace the three ``print`` lines at the bottom with:

.. code-block:: python

   result = register_user("bob@example.com", "password123")

   if result.is_success():
       user_data = result.value
       print(f"User created: {user_data['email']}")
   else:
       error = result.error
       print(f"Registration failed: {error}")

   result = register_user("invalid", "password123")

   if result.is_success():
       user_data = result.value
       print(f"User created: {user_data['email']}")
   else:
       error = result.error
       print(f"Registration failed: {error}")

Run the file:

.. code-block:: bash

   python registration.py

You should see:

.. code-block:: text

   User created: bob@example.com
   Registration failed: Invalid email format

Step 7: Lift a Throwing Function with Result.catch
---------------------------------------------------

So far every validation we wrote returns a ``Result`` by hand. But a lot of real
code — including the standard library — signals failure by *raising* an
exception. Suppose registration also accepts an age, supplied as a string from a
web form, that we need to parse with ``int()``. Calling ``int("abc")`` raises a
``ValueError``.

Rather than wrap that call in a ``try/except`` ourselves, we can use
``Result.catch``. It is a decorator that converts a function raising a given
exception type into one that returns a ``Result``. Add this to ``registration.py``:

.. code-block:: python

   @Result.catch(ValueError)
   def parse_age(raw: str) -> int:
       return int(raw)

   print(parse_age("30"))
   print(parse_age("not a number"))

Run the file:

.. code-block:: bash

   python registration.py

You should see:

.. code-block:: text

   Success(30)
   Failure(ValueError("invalid literal for int() with base 10: 'not a number'"))

The decorated ``parse_age`` returns an ordinary ``Result``, so it drops straight
into the same pipeline as our hand-written validations. Only ``ValueError`` is
turned into a ``Failure`` — any other exception would propagate normally. Replace
the two ``print`` lines to chain the parsed age into a range check:

.. code-block:: python

   def check_age_range(age: int) -> Result[Exception, int]:
       if 0 <= age <= 150:
           return Result[Exception, int].Success(age)
       return Result[Exception, int].Failure(ValueError("Age out of range"))

   print(parse_age("30") | check_age_range)
   print(parse_age("999") | check_age_range)
   print(parse_age("abc") | check_age_range)

Run the file:

.. code-block:: bash

   python registration.py

You should see:

.. code-block:: text

   Success(30)
   Failure(ValueError('Age out of range'))
   Failure(ValueError("invalid literal for int() with base 10: 'abc'"))

``Result.catch`` is the bridge between exception-raising code and the
``Result``-based pipelines you have been building — without a single
``try/except``. For more patterns, including how to recover the exact line that
caused a failure, see :doc:`../how-to/catch-exceptions`.

What We Built
-------------

We built a complete user registration system that validates email format, password length, and password strength, chains validations with ``|``, and uses ``@do`` to combine multiple results into a single function. We also used ``Result.catch`` to lift an exception-throwing function into the same pipeline. Every possible error is captured in the ``Result`` type and never thrown as an exception.
