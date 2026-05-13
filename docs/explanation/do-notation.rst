Understanding Do-Notation
=========================

This article explains the theory and design behind do-notation in Katharos, how it relates to Haskell's do-notation, and why it makes monadic code more readable.

What is Do-Notation?
--------------------

Do-notation is syntactic sugar for monadic bind operations. Instead of writing nested lambda functions with the bind operator (``|``), do-notation allows you to write monadic code in a more imperative, sequential style.

The Problem It Solves
---------------------

Monadic Nesting
~~~~~~~~~~~~~~~

When you chain multiple monadic operations where each step depends on previous results, you end up with nested lambdas:

.. code-block:: python

   result = m1 | (lambda x: 
                m2 | (lambda y:
                    m3 | (lambda z:
                        M.ret(f(x, y, z)))))

This pattern has several issues:

- **Readability**: Deep nesting makes it hard to follow the logic
- **Maintenance**: Adding or removing steps requires careful bracket management
- **Cognitive load**: You must track variable scope across nested closures
- **Error-prone**: Easy to make mistakes with parentheses and indentation

The Desugaring Process
----------------------

Do-notation is purely syntactic sugar. The compiler/interpreter transforms it into the nested bind operations behind the scenes.

Simple Example
~~~~~~~~~~~~~~

This do-notation code:

.. code-block:: python

   with Do[Maybe]() as do:
       x = do.arrow(m1)
       y = do.arrow(m2)
       result = do.ret(lambda x, y: x + y, x=x, y=y)

Desugars to:

.. code-block:: python

   result = m1 | (lambda x: 
                m2 | (lambda y: 
                    Maybe.ret(x + y)))

Complex Example
~~~~~~~~~~~~~~~

A more complex chain:

.. code-block:: python

   with Do[Maybe]() as do:
       a = do.arrow(get_user(1))
       b = do.arrow(get_manager(a))
       c = do.arrow(get_department(b))
       result = do.ret(format_info, user=a, mgr=b, dept=c)

Desugars to:

.. code-block:: python

   result = get_user(1) | (lambda a:
                get_manager(a) | (lambda b:
                    get_department(b) | (lambda c:
                        Maybe.ret(format_info(a, b, c)))))

Comparison with Haskell
------------------------

Haskell's Do-Notation
~~~~~~~~~~~~~~~~~~~~~

Haskell has built-in do-notation syntax:

.. code-block:: haskell

   do
     x <- m1
     y <- m2
     return (x + y)

Katharos's Do-Notation
~~~~~~~~~~~~~~~~~~~~~~

Python doesn't have syntax extension capabilities like Haskell, so Katharos uses a context manager:

.. code-block:: python

   with Do[Maybe]() as do:
       x = do.arrow(m1)
       y = do.arrow(m2)
       result = do.ret(lambda x, y: x + y, x=x, y=y)

Key Differences
~~~~~~~~~~~~~~~

1. **Syntax**: Haskell uses ``<-`` for bind, Katharos uses ``do.arrow()``
2. **Return**: Haskell uses ``return``, Katharos uses ``do.ret()``
3. **Scope**: Haskell's do-notation is language-level, Katharos uses Python's context managers
4. **Explicit parameters**: Katharos requires explicit parameter passing to ``ret()`` due to Python's scoping rules

Why These Design Choices?
--------------------------

Context Manager
~~~~~~~~~~~~~~~

Python doesn't allow syntax extensions, so we use context managers (``with`` statements) to create a scope for do-notation. This is idiomatic Python and integrates well with the language.

Explicit Parameters
~~~~~~~~~~~~~~~~~~~

In Haskell, variables in do-notation are automatically in scope:

.. code-block:: haskell

   do
     x <- m1
     y <- m2
     return (x + y)  -- x and y are automatically available

Python's scoping rules don't work the same way. To maintain referential transparency and avoid magic, Katharos requires explicit parameter passing:

.. code-block:: python

   with Do[Maybe]() as do:
       x = do.arrow(m1)
       y = do.arrow(m2)
       result = do.ret(lambda x, y: x + y, x=x, y=y)

This is more verbose but:

- Makes data flow explicit
- Avoids hidden state or magic
- Works with Python's type system
- Maintains functional programming principles

The arrow Method
~~~~~~~~~~~~~~~~

The name ``arrow`` comes from the ``<-`` operator in Haskell (which looks like an arrow). It represents binding a monadic value to a variable.

The ret and eval Methods
~~~~~~~~~~~~~~~~~~~~~~~~

- ``ret`` (return): Wraps a pure function's result in the monad
- ``eval`` (evaluate): Uses when your function already returns a monad

This distinction is necessary because Python is not lazy like Haskell, and we need to know whether to wrap the result or not.

Theoretical Foundation
----------------------

Monad Laws
~~~~~~~~~~

Do-notation preserves the monad laws:

1. **Left Identity**: ``do { x <- return v; f x }`` ≡ ``f v``
2. **Right Identity**: ``do { x <- m; return x }`` ≡ ``m``
3. **Associativity**: Nested do-blocks can be flattened

In Katharos:

.. code-block:: python

   # Left Identity
   with Do[Maybe]() as do:
       x = do.arrow(Maybe.ret(5))
       result = do.eval(f, x=x)
   # Equivalent to: f(5)

   # Right Identity
   with Do[Maybe]() as do:
       x = do.arrow(m)
       result = do.ret(lambda x: x, x=x)
   # Equivalent to: m

Sequencing
~~~~~~~~~~

Do-notation enforces sequential evaluation of monadic effects. Each ``arrow`` call must complete before the next one executes. This is crucial for:

- Error handling (short-circuiting on failure)
- State management (ensuring state changes happen in order)
- IO operations (maintaining order of side effects)

Pure vs Monadic Functions
~~~~~~~~~~~~~~~~~~~~~~~~~~

Do-notation makes the distinction between pure and monadic functions explicit:

.. code-block:: python

   with Do[Maybe]() as do:
       x = do.arrow(monadic_function())  # Returns Maybe[T]
       y = pure_function(x)               # Returns T
       z = do.arrow(another_monadic())    # Returns Maybe[U]
       result = do.ret(combine, x=x, y=y, z=z)

This clarity helps reason about where effects occur and where pure computation happens.

Performance Considerations
--------------------------

Overhead
~~~~~~~~

Do-notation has minimal overhead compared to manual bind operations:

- The context manager setup is negligible
- The desugaring happens at runtime but is optimized
- No additional allocations beyond what bind would require

When to Avoid
~~~~~~~~~~~~~

For very simple chains (1-2 operations), the overhead of setting up a do-block may not be worth it:

.. code-block:: python

   # Overkill
   with Do[Maybe]() as do:
       x = do.arrow(m)
       result = do.ret(f, x=x)

   # Better
   result = m.fmap(f)

Limitations
-----------

Python Constraints
~~~~~~~~~~~~~~~~~~

Do-notation in Python cannot:

- Use regular Python control flow (``if``, ``for``, ``while``) directly
- Automatically capture variables without explicit passing
- Provide the same syntactic elegance as Haskell's built-in notation

These are fundamental limitations of working within Python's syntax and semantics.

Workarounds
~~~~~~~~~~~

For control flow, use monadic combinators:

.. code-block:: python

   # Instead of if in do-notation
   result = condition.if_else(
       lambda: do_this(),
       lambda: do_that()
   )

For loops, use monadic fold or traverse operations.

Design Philosophy
-----------------

Pragmatism Over Purity
~~~~~~~~~~~~~~~~~~~~~~

Katharos's do-notation prioritizes:

1. **Pythonic code**: Uses familiar Python constructs (context managers)
2. **Explicitness**: Makes data flow visible
3. **Type safety**: Works well with type checkers
4. **Practicality**: Solves real readability problems

Rather than trying to exactly replicate Haskell's syntax, it adapts the concept to Python's strengths.

Gradual Adoption
~~~~~~~~~~~~~~~~

You can mix do-notation with bind operations:

.. code-block:: python

   # Start with bind
   result = m1 | f | g

   # Refactor complex parts to do-notation
   with Do[Maybe]() as do:
       x = do.arrow(m1 | f)
       y = do.arrow(complex_operation(x))
       result = do.ret(g, y=y)

This allows incremental adoption without rewriting entire codebases.

Conclusion
----------

Do-notation is a powerful tool for making monadic code readable and maintainable. While it can't replicate Haskell's syntax exactly due to Python's constraints, it successfully brings the core benefits of do-notation to Python:

- ✅ Eliminates nested lambdas
- ✅ Makes sequential monadic operations clear
- ✅ Maintains functional programming principles
- ✅ Integrates naturally with Python

Understanding the theory behind do-notation helps you use it effectively and know when to reach for it versus simpler alternatives like bind or fmap.

See Also
--------

- :doc:`../tutorials/do-syntax` - Practical tutorial
- :doc:`../how-to/do-notation` - Usage guide
- :doc:`monad-laws` - Theoretical foundation
- :doc:`../how-to/refactor-to-do` - Migration guide
