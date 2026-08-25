Validate a User Registration with Result
========================================

In this tutorial, you will build a registration validator that returns either
validated user data or a specific error. You will apply ``fmap``, the ``|``
operator, and do-notation to ``Result`` values, then display the final outcome.

.. note::

   The email and password rules in this tutorial are intentionally simple.
   They demonstrate ``Result`` and are not production authentication rules.

Prerequisites
-------------

- Complete the :doc:`do-syntax` tutorial. It introduces ``fmap``, the ``|``
  operator, and do-notation.
- Be familiar with Python dictionaries, functions, and type hints.

Step 1: Return Your First Result
--------------------------------

Create a file called ``registration.py`` with the following contents:

.. code-block:: python

   from katharos.types import Result

   def check_password_length(password: str) -> Result[ValueError, str]:
       if len(password) >= 8:
           return Result[ValueError, str].Success(password)
       return Result[ValueError, str].Failure(ValueError("Password too short"))

   print(check_password_length("secret123"))
   print(check_password_length("short"))

Run the file:

.. code-block:: bash

   python registration.py

You should see:

.. code-block:: text

   Success('secret123')
   Failure(ValueError('Password too short'))

``Success`` contains the accepted password. ``Failure`` contains the error
instead of raising it.

.. note::

   This tutorial supplies both type arguments when constructing a ``Result``.
   For example, ``Result[ValueError, str]`` tells a type checker the error and
   success types. The arguments are not required for the code to run.

Step 2: Add Email Validation
----------------------------

Remove the two ``print`` lines. Add this function and the new calls at the
bottom of ``registration.py``:

.. code-block:: python

   def check_email_format(email: str) -> Result[ValueError, str]:
       if "@" in email and "." in email:
           return Result[ValueError, str].Success(email)
       return Result[ValueError, str].Failure(ValueError("Invalid email format"))

   print(check_email_format("user@example.com"))
   print(check_email_format("notanemail"))

Run the file:

.. code-block:: bash

   python registration.py

You should see:

.. code-block:: text

   Success('user@example.com')
   Failure(ValueError('Invalid email format'))

Both validation functions now describe their possible failure in their return
type.

Step 3: Normalize a Successful Email
------------------------------------

Replace the two ``print`` lines with:

.. code-block:: python

   print(check_email_format("User@Example.COM").fmap(str.lower))
   print(check_email_format("invalid").fmap(str.lower))

Run the file:

.. code-block:: bash

   python registration.py

You should see:

.. code-block:: text

   Success('user@example.com')
   Failure(ValueError('Invalid email format'))

``fmap`` lowercases the successful email and leaves the failure unchanged.

Step 4: Chain Password Checks
-----------------------------

Remove the two ``print`` lines. Add this function and the new calls at the
bottom of ``registration.py``:

.. code-block:: python

   def check_password_strength(password: str) -> Result[ValueError, str]:
       if any(character.isdigit() for character in password):
           return Result[ValueError, str].Success(password)
       return Result[ValueError, str].Failure(
           ValueError("Password must contain a number")
       )

   print(check_password_length("secret123") | check_password_strength)
   print(check_password_length("secretword") | check_password_strength)
   print(check_password_length("short") | check_password_strength)

Run the file:

.. code-block:: bash

   python registration.py

You should see:

.. code-block:: text

   Success('secret123')
   Failure(ValueError('Password must contain a number'))
   Failure(ValueError('Password too short'))

The ``|`` operator runs the strength check only after the length check
succeeds. The first ``Failure`` stops the chain.

Step 5: Combine the Registration Checks
---------------------------------------

Add this import below the existing import at the top of ``registration.py``:

.. code-block:: python

   from katharos.syntax_sugar import DoBlock, do

Remove the three ``print`` lines. Add the registration function and new calls
at the bottom of the file:

.. code-block:: python

   @do(Result)
   def register_user(
       email: str,
       password: str,
   ) -> DoBlock[Result, dict[str, str]]:
       validated_email: str = yield check_email_format(email).fmap(str.lower)
       validated_password: str = yield (
           check_password_length(password) | check_password_strength
       )
       return {"email": validated_email, "password": validated_password}

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

Each ``yield`` gives the function a validated value. The first ``Failure``
stops the function, while the final dictionary is lifted into ``Success``.

Step 6: Report the Registration Outcome
---------------------------------------

Replace the three ``print`` lines with this reporting function and four calls:

.. code-block:: python

   def report_registration(
       result: Result[ValueError, dict[str, str]],
   ) -> None:
       if result.is_success():
           print(f"User created: {result.value['email']}")
       else:
           print(f"Registration failed: {result.error}")

   report_registration(register_user("Bob@Example.com", "password123"))
   report_registration(register_user("invalid", "password123"))
   report_registration(register_user("bob@example.com", "password"))
   report_registration(register_user("bob@example.com", "short"))

Run the completed program:

.. code-block:: bash

   python registration.py

You should see:

.. code-block:: text

   User created: bob@example.com
   Registration failed: Invalid email format
   Registration failed: Password must contain a number
   Registration failed: Password too short

``is_success`` selects the safe property to read: ``value`` for a success or
``error`` for a failure.

What You Built
--------------

You built a registration validator that:

- Represents accepted values with ``Success`` and validation errors with
  ``Failure``.
- Transforms a successful email with ``fmap``.
- Stops password validation at the first failure with ``|``.
- Combines dependent validation steps with ``@do(Result)``.
- Reports successful and failed registrations without raising the validation
  errors.

Next Steps
----------

- Continue with :doc:`immutable-lists` to work with immutable collections.
- See :doc:`../how-to/catch-exceptions` to convert exception-raising functions
  with ``Result.catch``.
- Consult the :doc:`../reference/api/types` for the complete ``Result`` API.
