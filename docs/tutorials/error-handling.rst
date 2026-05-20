Build a User Registration System with Result
============================================

In this tutorial, we will build a user registration system that handles errors functionally. By the end, you will have a working system that validates user input and creates user accounts without using exceptions.

Step 1: Create Your First Result
---------------------------------

First, we will create a simple function that returns a ``Result``. Create a new Python file called ``registration.py`` and add this code:

.. code-block:: python

   from katharos.types import Result

   def check_password_length(password: str) -> Result[Exception, str]:
       if len(password) >= 8:
           return Result[Exception, str].Success(password)
       return Result[Exception, str].Failure(ValueError("Password too short"))

Now run this code:

.. code-block:: python

   result = check_password_length("secret123")
   print(result)

You should see ``Success(secret123)``. Notice how the ``Result`` wraps the password when it's valid.

Now try with a short password:

.. code-block:: python

   result = check_password_length("short")
   print(result)

You should see ``Failure(ValueError('Password too short'))``. The error is captured inside the ``Result`` instead of being thrown.

Step 2: Add Email Validation
-----------------------------

Now we will add another validation function. Add this to your file:

.. code-block:: python

   def check_email_format(email: str) -> Result[Exception, str]:
       if "@" in email and "." in email:
           return Result[Exception, str].Success(email)
       return Result[Exception, str].Failure(ValueError("Invalid email format"))

Test it:

.. code-block:: python

   result = check_email_format("user@example.com")
   print(result)

You should see ``Success(user@example.com)``.

Try an invalid email:

.. code-block:: python

   result = check_email_format("notanemail")
   print(result)

You should see ``Failure(ValueError('Invalid email format'))``.

Step 3: Transform Success Values
---------------------------------

We will now transform the email to lowercase. Add this code:

.. code-block:: python

   result = check_email_format("User@Example.COM").fmap(lambda email: email.lower())
   print(result)

You should see ``Success(user@example.com)``. The ``fmap`` method applies the function only if the ``Result`` is a success.

Now try with an invalid email:

.. code-block:: python

   result = check_email_format("invalid").fmap(lambda email: email.lower())
   print(result)

You should see ``Failure(ValueError('Invalid email format'))``. Notice that the function was never called because the ``Result`` was already a failure.

Step 4: Chain Validations Together
-----------------------------------

Now we will chain multiple validations. Add this function:

.. code-block:: python

   def check_password_strength(password: str) -> Result[Exception, str]:
       if any(c.isdigit() for c in password):
           return Result[Exception, str].Success(password)
       return Result[Exception, str].Failure(ValueError("Password must contain a number"))

Chain the password validations using the ``|`` operator:

.. code-block:: python

   result = (
       check_password_length("secret123")
       | check_password_strength
   )
   print(result)

You should see ``Success(secret123)``. Both validations passed.

Now try a password that fails the second check:

.. code-block:: python

   result = (
       check_password_length("secretword")
       | check_password_strength
   )
   print(result)

You should see ``Failure(ValueError('Password must contain a number'))``. The chain stopped at the first failure.

Step 5: Build the Registration Function
----------------------------------------

Now we will combine everything into a registration function. Add this code:

.. code-block:: python

   from katharos.syntax_sugar import Do

   def register_user(email: str, password: str) -> Result[Exception, dict]:
       with Do[Result]() as do:
           validated_email = do.arrow(
               check_email_format(email).fmap(lambda e: e.lower())
           )
           validated_password = do.arrow(
               check_password_length(password) | check_password_strength
           )
           user = do.ret(
               lambda e, p: {"email": e, "password": p},
               e=validated_email,
               p=validated_password,
           )
       return user

Test it with valid input:

.. code-block:: python

   user = register_user("Alice@Example.com", "secret123")
   print(user)

You should see ``Success({'email': 'alice@example.com', 'password': 'secret123'})``.

Try with an invalid email:

.. code-block:: python

   user = register_user("notanemail", "secret123")
   print(user)

You should see ``Failure(ValueError('Invalid email format'))``. The function stopped at the first error.

Try with an invalid password:

.. code-block:: python

   user = register_user("alice@example.com", "short")
   print(user)

You should see ``Failure(ValueError('Password too short'))`` or similar.

Step 6: Extract Values from Results
------------------------------------

Now we will extract the user data when registration succeeds. Add this code:

.. code-block:: python

   result = register_user("bob@example.com", "password123")
   
   if result.is_success():
       user_data = result.value
       print(f"User created: {user_data['email']}")
   else:
       error = result.error
       print(f"Registration failed: {error}")

Run this code. You should see ``User created: bob@example.com``.

Now try with invalid data:

.. code-block:: python

   result = register_user("invalid", "password123")
   
   if result.is_success():
       user_data = result.value
       print(f"User created: {user_data['email']}")
   else:
       error = result.error
       print(f"Registration failed: {error}")

You should see ``Registration failed: Invalid email format``.


What We Built
-------------

We built a complete user registration system that:

- Validates email format
- Validates password length
- Validates password strength
- Chains validations together
- Returns explicit success or failure
- Never throws exceptions

The ``Result`` type made every possible error visible in the function signatures, and the ``|`` operator let us chain validations cleanly.

