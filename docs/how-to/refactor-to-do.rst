How to Refactor to Do-Notation
================================

This guide shows you how to refactor existing monadic code that uses bind operations into cleaner do-notation.

When to Refactor
----------------

Consider refactoring to do-notation when you have:

- **3+ chained bind operations** that are hard to read
- **Nested lambdas** that capture multiple variables
- **Complex logic** where intermediate values are reused
- **Code reviews** where reviewers struggle to understand the flow

Don't refactor if:

- You have simple 1-2 operation chains
- The bind chain is already clear and readable
- You're using point-free style intentionally

Step-by-Step Refactoring
-------------------------

Step 1: Identify the Pattern
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Look for nested bind operations with lambdas:

.. code-block:: python

   result = m1 | (lambda x: m2 | (lambda y: m3 | (lambda z: M.ret(f(x, y, z)))))

Step 2: Set Up the Do Block
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a do-notation context with the appropriate monad type:

.. code-block:: python

   with Do[M]() as do:
       # Code will go here
       pass

Step 3: Convert Each Bind
~~~~~~~~~~~~~~~~~~~~~~~~~~

Replace each ``| (lambda var: ...)`` with ``var = do.arrow(...)``:

.. code-block:: python

   with Do[M]() as do:
       x = do.arrow(m1)
       y = do.arrow(m2)
       z = do.arrow(m3)

Step 4: Convert the Return
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Replace the final ``M.ret(...)`` with ``do.ret(...)``:

.. code-block:: python

   with Do[M]() as do:
       x = do.arrow(m1)
       y = do.arrow(m2)
       z = do.arrow(m3)
       result = do.ret(f, x=x, y=y, z=z)

Complete Example
~~~~~~~~~~~~~~~~

Before:

.. code-block:: python

   result = m1 | (lambda x: m2 | (lambda y: m3 | (lambda z: M.ret(f(x, y, z)))))

After:

.. code-block:: python

   with Do[M]() as do:
       x = do.arrow(m1)
       y = do.arrow(m2)
       z = do.arrow(m3)
       result = do.ret(f, x=x, y=y, z=z)

Real-World Examples
-------------------

Example 1: User Lookup Chain
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Before:**

.. code-block:: python

   from katharos.types import Maybe

   def get_user(user_id: int) -> Maybe[dict]: ...
   def get_manager_id(user: dict) -> Maybe[int]: ...

   result = (
       get_user(1)
       | get_manager_id
       | get_user
       | get_manager_id
       | get_user
       | (lambda mgr: Maybe.ret(mgr["name"]))
   )

**After:**

.. code-block:: python

   from katharos.types import Maybe
   from katharos.syntax_sugar import Do

   with Do[Maybe]() as do:
       user = do.arrow(get_user(1))
       mgr_id_1 = do.arrow(do.eval(get_manager_id, user=user))
       mgr_1 = do.arrow(do.eval(get_user, user_id=mgr_id_1))
       mgr_id_2 = do.arrow(do.eval(get_manager_id, user=mgr_1))
       mgr_2 = do.arrow(do.eval(get_user, user_id=mgr_id_2))
       result = do.ret(lambda mgr: mgr["name"], mgr=mgr_2)

**Benefits:**

- Clear variable names show the data flow
- Easy to see each step in the chain
- Simple to add logging or debugging between steps

Example 2: Validation Pipeline
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Before:**

.. code-block:: python

   from katharos.types import Result

   def validate_email(email: str) -> Result[ValueError, str]: ...
   def validate_age(age: int) -> Result[ValueError, int]: ...
   def validate_name(name: str) -> Result[ValueError, str]: ...

   result = (
       validate_email(email)
       | (lambda e: validate_age(age)
          | (lambda a: validate_name(name)
             | (lambda n: Result.ret({"email": e, "age": a, "name": n}))))
   )

**After:**

.. code-block:: python

   from katharos.types import Result
   from katharos.syntax_sugar import Do

   with Do[Result]() as do:
       valid_email = do.arrow(validate_email(email))
       valid_age = do.arrow(validate_age(age))
       valid_name = do.arrow(validate_name(name))
       result = do.ret(
           lambda e, a, n: {"email": e, "age": a, "name": n},
           e=valid_email,
           a=valid_age,
           n=valid_name
       )

**Benefits:**

- All validations are clearly visible
- Easy to add more validation steps
- Clear what data goes into the final result

Example 3: Complex Calculation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Before:**

.. code-block:: python

   from katharos.types import Maybe

   def safe_divide(a: float, b: float) -> Maybe[float]: ...
   def safe_sqrt(x: float) -> Maybe[float]: ...
   def safe_log(x: float) -> Maybe[float]: ...

   result = (
       safe_divide(100, 4)
       | (lambda x: safe_sqrt(x)
          | (lambda y: safe_log(y)
             | (lambda z: Maybe.ret(z * 10))))
   )

**After:**

.. code-block:: python

   from katharos.types import Maybe
   from katharos.syntax_sugar import Do

   with Do[Maybe]() as do:
       quotient = do.arrow(safe_divide(100, 4))
       root = do.arrow(do.eval(safe_sqrt, x=quotient))
       log_val = do.arrow(do.eval(safe_log, x=root))
       result = do.ret(lambda val: val * 10, val=log_val)

**Benefits:**

- Descriptive variable names explain each step
- Easy to understand the mathematical operations
- Simple to modify the calculation

Example 4: Mixed Pure and Monadic
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Before:**

.. code-block:: python

   from katharos.types import Maybe

   def get_user(id: int) -> Maybe[dict]: ...
   def calculate_discount(age: int) -> float: ...  # Pure function

   result = (
       get_user(1)
       | (lambda user: Maybe.ret(calculate_discount(user["age"]))
          | (lambda discount: Maybe.ret({
              "user": user["name"],
              "discount": discount
          })))
   )

**After:**

.. code-block:: python

   from katharos.types import Maybe
   from katharos.syntax_sugar import Do

   with Do[Maybe]() as do:
       user = do.arrow(get_user(1))
       result = do.ret(
           lambda u: {"user": u["name"], "discount": calculate_discount(u["age"])},
           u=user
       )

**Benefits:**

- Clear distinction between monadic and pure operations
- No unnecessary wrapping/unwrapping
- More efficient code

Common Patterns
---------------

Pattern 1: Sequential Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When each step depends on the previous:

.. code-block:: python

   # Before
   result = m1 | (lambda a: f(a) | (lambda b: g(b) | (lambda c: M.ret(c))))

   # After
   with Do[M]() as do:
       a = do.arrow(m1)
       b = do.arrow(do.eval(f, a=a))
       c = do.arrow(do.eval(g, b=b))
       result = do.ret(lambda x: x, x=c)

Pattern 2: Parallel Binds
~~~~~~~~~~~~~~~~~~~~~~~~~~

When steps don't depend on each other:

.. code-block:: python

   # Before
   result = m1 | (lambda x: m2 | (lambda y: m3 | (lambda z: M.ret(f(x, y, z)))))

   # After
   with Do[M]() as do:
       x = do.arrow(m1)
       y = do.arrow(m2)
       z = do.arrow(m3)
       result = do.ret(f, x=x, y=y, z=z)

Pattern 3: Conditional Logic
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When you need to make decisions based on monadic values:

.. code-block:: python

   # Before
   result = m1 | (lambda x: m2(x) if x > 0 else m3(x))

   # After
   with Do[M]() as do:
       x = do.arrow(m1)
       result = do.eval(lambda val: m2(val) if val > 0 else m3(val), val=x)

Pattern 4: Reusing Values
~~~~~~~~~~~~~~~~~~~~~~~~~

When you need to use a value multiple times:

.. code-block:: python

   # Before (awkward)
   result = m1 | (lambda x: m2 | (lambda y: M.ret(f(x, x, y))))

   # After (clear)
   with Do[M]() as do:
       x = do.arrow(m1)
       y = do.arrow(m2)
       result = do.ret(lambda x_val, y_val: f(x_val, x_val, y_val), x_val=x, y_val=y)

Handling Edge Cases
-------------------

Monadic Return Values
~~~~~~~~~~~~~~~~~~~~~

If your final function returns a monad, use ``eval`` instead of ``ret``:

.. code-block:: python

   # Before
   result = m1 | (lambda x: m2 | (lambda y: final_monadic_func(x, y)))

   # After
   with Do[M]() as do:
       x = do.arrow(m1)
       y = do.arrow(m2)
       result = do.eval(lambda x_val, y_val: final_monadic_func(x_val, y_val), x_val=x, y_val=y)

Ignoring Values
~~~~~~~~~~~~~~~

When you need to execute a monadic action but don't use its value:

.. code-block:: python

   # Before
   result = m1 | (lambda _: m2 | (lambda x: M.ret(x)))

   # After
   with Do[M]() as do:
       do.arrow(m1)  # Execute but don't bind
       x = do.arrow(m2)
       result = do.ret(lambda x: x, x=x)

Nested Do Blocks
~~~~~~~~~~~~~~~~

You can nest do blocks when needed:

.. code-block:: python

   with Do[Maybe]() as do:
       x = do.arrow(m1)
       
       # Nested computation
       with Do[Maybe]() as inner_do:
           y = inner_do.arrow(m2)
           z = inner_do.arrow(m3)
           inner_result = inner_do.ret(lambda y_val, z_val: y_val + z_val, y_val=y, z_val=z)
       
       final = do.arrow(inner_result)
       result = do.ret(lambda x_val, f_val: x_val + f_val, x_val=x, f_val=final)

Testing Strategy
----------------

Test Before and After
~~~~~~~~~~~~~~~~~~~~~

Keep your tests and verify behavior doesn't change:

.. code-block:: python

   def test_user_lookup():
       # Test the original implementation
       result_before = original_implementation(1)
       
       # Refactor to do-notation
       result_after = refactored_implementation(1)
       
       # Verify they're equivalent
       assert result_before == result_after

Incremental Refactoring
~~~~~~~~~~~~~~~~~~~~~~~

Refactor one function at a time:

1. Write tests for the current implementation
2. Refactor to do-notation
3. Run tests to verify correctness
4. Move to the next function

This minimizes risk and makes it easier to identify issues.

Performance Considerations
--------------------------

Do-notation has minimal overhead, but be aware:

- **No performance penalty** for most use cases
- **Slightly more allocations** due to context manager setup
- **Same asymptotic complexity** as manual bind operations

Benchmark if performance is critical:

.. code-block:: python

   import timeit

   # Benchmark bind version
   time_bind = timeit.timeit(lambda: bind_version(), number=10000)

   # Benchmark do-notation version
   time_do = timeit.timeit(lambda: do_version(), number=10000)

   print(f"Bind: {time_bind:.4f}s, Do: {time_do:.4f}s")

Migration Checklist
-------------------

Before refactoring:

- ☐ Identify complex bind chains (3+ operations)
- ☐ Ensure you have tests for existing behavior
- ☐ Understand the data flow in the current code

During refactoring:

- ☐ Import ``Do`` from ``katharos.syntax_sugar``
- ☐ Set up do block with correct monad type
- ☐ Convert each bind to ``arrow``
- ☐ Convert final return to ``ret`` or ``eval``
- ☐ Pass all variables explicitly to ``ret``/``eval``

After refactoring:

- ☐ Run all tests to verify correctness
- ☐ Review for readability improvements
- ☐ Update documentation if needed
- ☐ Consider adding type annotations

Common Mistakes
---------------

Forgetting to Pass Variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Wrong - trying to use DoVariable directly
   with Do[Maybe]() as do:
       x = do.arrow(m1)
       result = do.ret(lambda: x * 2)  # x is a DoVariable, not the value!

   # Correct - pass DoVariable to ret, function receives unwrapped value
   with Do[Maybe]() as do:
       x = do.arrow(m1)
       result = do.ret(lambda x_val: x_val * 2, x_val=x)

Using ret for Monadic Functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Wrong - monadic_func returns Maybe
   with Do[Maybe]() as do:
       x = do.arrow(m1)
       result = do.ret(monadic_func, x_val=x)

   # Correct - use eval for functions that return monads
   with Do[Maybe]() as do:
       x = do.arrow(m1)
       result = do.eval(lambda x_val: monadic_func(x_val), x_val=x)

Wrong Monad Type
~~~~~~~~~~~~~~~~

.. code-block:: python

   # Wrong - using Maybe but m1 is Result
   with Do[Maybe]() as do:
       x = do.arrow(m1)  # m1: Result[T, E]

   # Correct
   with Do[Result]() as do:
       x = do.arrow(m1)

Conclusion
----------

Refactoring to do-notation improves code readability and maintainability. Follow these guidelines:

1. **Start small**: Refactor simple chains first
2. **Test thoroughly**: Ensure behavior doesn't change
3. **Be consistent**: Use do-notation for similar patterns across your codebase
4. **Know when to stop**: Don't force do-notation where bind is clearer

See Also
--------

- :doc:`../tutorials/do-syntax` - Learn do-notation from scratch
- :doc:`do-notation` - Usage guide
- :doc:`../explanation/do-notation` - Theory and design
- :doc:`chain-operations` - Alternative patterns
