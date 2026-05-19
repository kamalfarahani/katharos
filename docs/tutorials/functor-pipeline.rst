Building Pipelines with Functors
=================================

Learn how to build data transformation pipelines using functors and function composition.

What You'll Learn
-----------------

- How functors enable safe data transformations with ``fmap``
- Building pipelines by chaining ``fmap`` operations
- Working with different functor types (``Maybe``, ``Result``, ``ImmutableList``)
- Composing pure functions for reusable pipelines

Prerequisites
-------------

Complete the :doc:`getting-started` tutorial to understand ``Maybe`` and ``fmap``.

The Functor Pattern
--------------------

A **functor** is a type that implements ``fmap``, allowing you to map functions over its contents without unwrapping the value. This is the foundation of functional pipelines.

The ``Functor`` interface has two laws:

- **Identity**: ``fmap(id) = id`` — mapping the identity function does nothing
- **Composition**: ``fmap(g . f) = fmap(g) . fmap(f)`` — mapping composed functions equals chaining ``fmap`` calls

Let's see this in action:

.. code-block:: python

   from katharos.types import Maybe
   from katharos.functools import F

   # Identity law: fmap(id) = id
   x = Maybe.Just(5)
   assert x.fmap(F.id) == x

   # Composition law: fmap(g . f) = fmap(g) . fmap(f)
   f = lambda a: a * 2
   g = lambda b: b + 10
   assert x.fmap(F.compose(g)(f)) == x.fmap(f).fmap(g)

Building a Simple Pipeline
---------------------------

The simplest pipeline chains multiple ``fmap`` calls to transform data step by step:

.. code-block:: python

   from katharos.types import Maybe

   def parse_int(s: str) -> Maybe[int]:
       try:
           return Maybe.Just(int(s))
       except ValueError:
           return Maybe.Nothing()

   def is_even(n: int) -> bool:
       return n % 2 == 0

   def double(n: int) -> int:
       return n * 2

   # Build a pipeline: parse -> check if even -> double
   user_input = "42"
   result = (
       parse_int(user_input)
       .fmap(double)           # 42 -> 84
       .fmap(lambda x: x + 1)  # 84 -> 85
   )
   print(result)  # Just(85)

   # If parsing fails, the entire pipeline short-circuits
   bad_input = "not a number"
   result = (
       parse_int(bad_input)
       .fmap(double)
       .fmap(lambda x: x + 1)
   )
   print(result)  # Nothing()

Key insight: when ``parse_int`` returns ``Nothing``, all subsequent ``fmap`` calls are skipped. This prevents errors and makes error handling implicit.

Pipelines with Result
---------------------

The ``Result`` type is perfect for pipelines that need to track error details:

.. code-block:: python

   from katharos.types import Result

   def validate_age(age: int) -> Result[Exception, int]:
       if age < 0 or age > 150:
           return Result.Failure(ValueError(f"Invalid age: {age}"))
       return Result.Success(age)

   def calculate_birth_year(age: int) -> int:
       from datetime import datetime
       return datetime.now().year - age

   def format_info(birth_year: int) -> str:
       return f"You were born around {birth_year}"

   # Pipeline: validate -> calculate -> format
   age = 30
   result = (
       validate_age(age)
       .fmap(calculate_birth_year)
       .fmap(format_info)
   )
   print(result)  # Success('You were born around 1996')

   # Invalid input propagates the error
   result = (
       validate_age(-5)
       .fmap(calculate_birth_year)
       .fmap(format_info)
   )
   print(result)  # Failure(ValueError('Invalid age: -5'))

Pipelines with ImmutableList
-----------------------------

``ImmutableList`` is a functor that applies transformations to every element:

.. code-block:: python

   from katharos.types import ImmutableList

   def square(x: int) -> int:
       return x ** 2

   def add_one(x: int) -> int:
       return x + 1

   # Pipeline: square all elements -> add one to each
   numbers = ImmutableList([1, 2, 3, 4])
   result = (
       numbers
       .fmap(square)      # [1, 4, 9, 16]
       .fmap(add_one)     # [2, 5, 10, 17]
   )
   print(result)  # ImmutableList([2, 5, 10, 17])

Composing Functions
--------------------

For more complex pipelines, you can compose functions before mapping:

.. code-block:: python

   from katharos.types import Maybe
   from katharos.functools import F

   def double(x: int) -> int:
       return x * 2

   def add_ten(x: int) -> int:
       return x + 10

   def to_string(x: int) -> str:
       return f"Result: {x}"

   # Compose functions: double -> add_ten -> to_string
   composed = F.compose(to_string)(F.compose(add_ten)(double))

   # Use the composed function in a pipeline
   result = Maybe.Just(5).fmap(composed)
   print(result)  # Just('Result: 20')

   # Equivalent to chaining fmap calls
   result = (
       Maybe.Just(5)
       .fmap(double)
       .fmap(add_ten)
       .fmap(to_string)
   )
   print(result)  # Just('Result: 20')

Real-World Example: Data Processing Pipeline
---------------------------------------------

Let's build a realistic pipeline that processes user data:

.. code-block:: python

   from katharos.types import Result
   from datetime import datetime

   def validate_email(email: str) -> Result[Exception, str]:
       if "@" not in email or "." not in email:
           return Result.Failure(ValueError(f"Invalid email: {email}"))
       return Result.Success(email)

   def extract_domain(email: str) -> str:
       return email.split("@")[1]

   def check_domain_length(domain: str) -> Result[Exception, str]:
       if len(domain) < 3:
           return Result.Failure(ValueError(f"Domain too short: {domain}"))
       return Result.Success(domain)

   def format_report(domain: str) -> str:
       return f"Email domain '{domain}' is valid (checked at {datetime.now().strftime('%Y-%m-%d')})"

   # Pipeline: validate email -> extract domain -> check domain -> format report
   email = "user@example.com"
   result = (
       validate_email(email)
       .fmap(extract_domain)           # "example.com"
   )
   # Note: check_domain_length returns a Result, so we need to use bind (|) instead of fmap
   # This is where monads come in - see the first-monad tutorial for details
   result = result | (lambda domain: check_domain_length(domain))
   result = result.fmap(format_report)

   print(result)  # Success("Email domain 'example.com' is valid (checked at ...)")

   # Invalid email short-circuits the pipeline
   result = (
       validate_email("invalid")
       .fmap(extract_domain)
       .fmap(format_report)
   )
   print(result)  # Failure(ValueError('Invalid email: invalid'))

When to Use Pipelines
---------------------

Use ``fmap`` pipelines when:

- ✅ Each transformation is a **pure function** (no side effects)
- ✅ You're transforming **one value** at a time
- ✅ You want to **short-circuit on failure** (with ``Maybe`` or ``Result``)
- ✅ You're applying the **same function to all elements** (with ``ImmutableList``)

Use **monadic bind** (``|``) when:

- You need to **chain operations that return functors** (see :doc:`first-monad`)
- You need to **use values from previous steps** in later steps
- You're building complex workflows (see :doc:`do-syntax`)

What You've Learned
-------------------

Congratulations! You now understand:

- ✅ How functors enable safe transformations with ``fmap``
- ✅ How to build pipelines by chaining ``fmap`` calls
- ✅ How different functor types handle transformations differently
- ✅ When to use pipelines vs. monadic bind operations

Next Steps
----------

- Learn about :doc:`first-monad` to handle operations that return functors
- Explore :doc:`do-syntax` for complex multi-step workflows
- Read :doc:`../explanation/fp-concepts` for deeper functional programming theory

Further Reading
---------------

- :class:`katharos.algebra.Functor` - Functor interface
- :class:`katharos.functools.F` - Utility functions for composition
- :doc:`../how-to/function-composition` - Advanced composition patterns
