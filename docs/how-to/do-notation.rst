How to Use Do-Notation
======================

Do-notation provides a cleaner syntax for complex monadic computations. This guide shows you how to use it effectively.

When to Use Do-Notation
------------------------

Use do-notation when you have:

- Multiple monadic operations that depend on each other
- Complex chains that are hard to read with ``|`` operators
- Need to use intermediate values multiple times

Basic Usage
-----------

Simple Example
~~~~~~~~~~~~~~

.. code-block:: python

   from katharos.types import Maybe
   from katharos.syntax_sugar import Do
   
   m1 = Maybe.Just(3)
   m2 = Maybe.Just(4)
   
   with Do[Maybe]() as do:
       x = do.arrow(m1)
       y = do.arrow(m2)
       result = do.ret(lambda x, y: x + y, x=x, y=y)
   
   print(result)  # Just(7)

Breaking It Down
~~~~~~~~~~~~~~~~

1. **Create a Do block:** ``with Do[Maybe]() as do:``
   
   Specify the monad type in brackets.

2. **Bind values:** ``x = do.arrow(m1)``
   
   Extract values from monads. Similar to ``<-`` in Haskell.

3. **Return result:** ``do.ret(lambda x, y: x + y, x=x, y=y)``
   
   Provide a function and the variables it uses.

Comparison with Bind
--------------------

Without Do-Notation
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from katharos.types import Maybe
   
   result = (
       Maybe.Just(3)
       | (lambda x: Maybe.Just(4)
          | (lambda y: Maybe.Just(x + y)))
   )

With Do-Notation
~~~~~~~~~~~~~~~~

.. code-block:: python

   from katharos.types import Maybe
   from katharos.syntax_sugar import Do
   
   with Do[Maybe]() as do:
       x = do.arrow(Maybe.Just(3))
       y = do.arrow(Maybe.Just(4))
       result = do.ret(lambda x, y: x + y, x=x, y=y)

The do-notation version is more readable, especially with more operations.

Practical Examples
------------------

User Lookup Chain
~~~~~~~~~~~~~~~~~

.. code-block:: python

   from katharos.types import Maybe
   from katharos.syntax_sugar import Do
   
   users = {
       1: {"name": "Alice", "manager_id": 2},
       2: {"name": "Bob", "manager_id": 3},
       3: {"name": "Charlie", "manager_id": None},
   }
   
   def get_user(user_id: int) -> Maybe[dict]:
       user = users.get(user_id)
       return Maybe.Nothing() if user is None else Maybe.Just(user)
   
   def get_manager_id(user: dict) -> Maybe[int]:
       manager_id = user.get("manager_id")
       return Maybe.Nothing() if manager_id is None else Maybe.Just(manager_id)
   
   # Find Alice's manager's manager
   with Do[Maybe]() as do:
       alice = do.arrow(get_user(1))
       alice_mgr_id = do.arrow(get_manager_id(alice))
       alice_mgr = do.arrow(get_user(alice_mgr_id))
       mgr_mgr_id = do.arrow(get_manager_id(alice_mgr))
       mgr_mgr = do.arrow(get_user(mgr_mgr_id))
       result = do.ret(lambda mgr_mgr: mgr_mgr["name"], mgr_mgr=mgr_mgr)
   
   print(result)  # Just('Charlie')

Complex Calculations
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from katharos.types import Result
   from katharos.syntax_sugar import Do
   
   def safe_divide(a: float, b: float) -> Result[Exception, float]:
       if b == 0:
           return Result.Failure(ZeroDivisionError("Division by zero"))
       return Result.Success(a / b)
   
   def safe_sqrt(x: float) -> Result[Exception, float]:
       if x < 0:
           return Result.Failure(ValueError("Negative square root"))
       return Result.Success(x ** 0.5)
   
   # Calculate: sqrt((a / b) + (c / d))
   with Do[Result]() as do:
       ab = do.arrow(safe_divide(10, 2))      # 5.0
       cd = do.arrow(safe_divide(20, 4))      # 5.0
       sum_val = do.ret(lambda ab, cd: ab + cd, ab=ab, cd=cd)  # 10.0
       final = do.arrow(safe_sqrt(sum_val.value))
       result = do.ret(lambda final: final, final=final)
   
   print(result)  # Success(3.1622776601683795)

Using eval Instead of ret
-------------------------

Use ``eval`` when your final function returns a monad:

.. code-block:: python

   from katharos.types import Maybe
   from katharos.syntax_sugar import Do
   
   def safe_sqrt(x: float) -> Maybe[float]:
       if x < 0:
           return Maybe.Nothing()
       return Maybe.Just(x ** 0.5)
   
   # Using eval for monadic return
   with Do[Maybe]() as do:
       x = do.arrow(Maybe.Just(16))
       y = do.arrow(Maybe.Just(9))
       sum_val = do.ret(lambda x, y: x + y, x=x, y=y)
       # eval because safe_sqrt returns Maybe
       result = do.eval(
           lambda sum_val: safe_sqrt(sum_val.value),
           sum_val=sum_val
       )
   
   print(result)  # Just(5.0)

**Rule of thumb:**
- Use ``ret`` when your function returns a plain value
- Use ``eval`` when your function returns a monad

Ignoring Intermediate Values
-----------------------------

Sometimes you need to execute a monadic action but don't use its value:

.. code-block:: python

   from katharos.types import IO
   from katharos.syntax_sugar import Do
   
   # Register but don't bind
   with Do[IO]() as do:
       do.arrow(IO(lambda: print("Step 1")))
       do.arrow(IO(lambda: print("Step 2")))
       x = do.arrow(IO(lambda: 42))
       result = do.ret(lambda x: x * 2, x=x)
   
   result.run()
   # Prints:
   # Step 1
   # Step 2
   # Returns: 84

Common Patterns
---------------

Conditional Logic
~~~~~~~~~~~~~~~~~

.. code-block:: python

   from katharos.types import Maybe
   from katharos.syntax_sugar import Do
   
   def validate_age(age: int) -> Maybe[int]:
       if age < 0 or age > 150:
           return Maybe.Nothing()
       return Maybe.Just(age)
   
   def validate_name(name: str) -> Maybe[str]:
       if not name or len(name) < 2:
           return Maybe.Nothing()
       return Maybe.Just(name)
   
   with Do[Maybe]() as do:
       age = do.arrow(validate_age(25))
       name = do.arrow(validate_name("Alice"))
       result = do.ret(
           lambda age, name: f"{name} is {age} years old",
           age=age,
           name=name
       )
   
   print(result)  # Just('Alice is 25 years old')

Multiple Computations
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from katharos.types import Maybe
   from katharos.syntax_sugar import Do
   
   with Do[Maybe]() as do:
       a = do.arrow(Maybe.Just(1))
       b = do.arrow(Maybe.Just(2))
       c = do.arrow(Maybe.Just(3))
       d = do.arrow(Maybe.Just(4))
       result = do.ret(
           lambda a, b, c, d: a + b + c + d,
           a=a, b=b, c=c, d=d
       )
   
   print(result)  # Just(10)

Error Handling
--------------

Do-notation automatically short-circuits on failure:

.. code-block:: python

   from katharos.types import Maybe
   from katharos.syntax_sugar import Do
   
   with Do[Maybe]() as do:
       x = do.arrow(Maybe.Just(5))
       y = do.arrow(Maybe.Nothing())  # Fails here
       z = do.arrow(Maybe.Just(10))   # Never executed
       result = do.ret(lambda x, y, z: x + y + z, x=x, y=y, z=z)
   
   print(result)  # Nothing()

Best Practices
--------------

1. **Keep blocks focused**
   
   Don't make do-blocks too long. Extract complex logic into functions.

2. **Use meaningful variable names**
   
   .. code-block:: python
   
      # Good
      with Do[Maybe]() as do:
          user = do.arrow(get_user(user_id))
          manager = do.arrow(get_manager(user))
          result = do.ret(lambda manager: manager.name, manager=manager)
      
      # Bad
      with Do[Maybe]() as do:
          x = do.arrow(get_user(user_id))
          y = do.arrow(get_manager(x))
          result = do.ret(lambda y: y.name, y=y)

3. **Prefer bind for simple chains**
   
   Do-notation is overkill for simple operations:
   
   .. code-block:: python
   
      # Overkill
      with Do[Maybe]() as do:
          x = do.arrow(Maybe.Just(5))
          result = do.ret(lambda x: x * 2, x=x)
      
      # Better
      result = Maybe.Just(5).fmap(lambda x: x * 2)

4. **Type annotations help**
   
   .. code-block:: python
   
      with Do[Maybe]() as do:
          x: int = do.arrow(Maybe.Just(5))
          result: Maybe[int] = do.ret(lambda x: x * 2, x=x)

Limitations
-----------

- Cannot use regular Python control flow (if/for/while) with do-notation
- All operations must be monadic
- Slightly more verbose than bind for simple cases

Troubleshooting
---------------

"Variable not found in do block"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Make sure you pass the variable to ``ret`` or ``eval``:

.. code-block:: python

   # Wrong
   with Do[Maybe]() as do:
       x = do.arrow(Maybe.Just(5))
       result = do.ret(lambda: x * 2)  # Missing x=x
   
   # Correct
   with Do[Maybe]() as do:
       x = do.arrow(Maybe.Just(5))
       result = do.ret(lambda x: x * 2, x=x)

"Do must be instantiated with a type parameter"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Always specify the monad type:

.. code-block:: python

   # Wrong
   with Do() as do:
       ...
   
   # Correct
   with Do[Maybe]() as do:
       ...

See Also
--------

- :class:`katharos.syntax_sugar.Do` - API reference
- :doc:`../tutorials/first-monad` - Understanding monads
- :doc:`chain-operations` - Alternative patterns
- :doc:`../explanation/monad-laws` - Theory behind monads
