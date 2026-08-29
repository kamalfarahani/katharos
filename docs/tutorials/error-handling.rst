Calculate an Order Subtotal with Result
=======================================

In this tutorial, you will build an order-subtotal calculator that reads JSON
input and returns either a calculated subtotal or the error that prevented the
calculation. You will create ``Success`` and ``Failure`` values, then combine
two ``Result``-returning functions with do-notation.

**Time:** About 15 minutes.

.. note::

   The JSON validation in this tutorial is intentionally small. It demonstrates
   ``Result`` and is not a complete order-validation system.

Prerequisites
-------------

- Complete the :doc:`do-syntax` tutorial.
- Be familiar with Python functions, dictionaries, exceptions, and type hints.

Step 1: Parse a Product Price
-----------------------------

Create a file called ``order_subtotal.py`` with the following contents:

.. code-block:: python

   import json

   from katharos.types import Result

   def parse_unit_price(product_json: str) -> Result[Exception, float]:
       """Read and validate a product's unit price."""
       try:
           unit_price = float(json.loads(product_json)["unit_price"])
           if unit_price < 0:
               raise ValueError("unit_price must not be negative")
           return Result[Exception, float].Success(unit_price)
       except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
           return Result[Exception, float].Failure(error)

   print(parse_unit_price('{"unit_price": 12.50}'))
   print(parse_unit_price('{"unit_price": -1}'))

Run the file:

.. code-block:: bash

   python order_subtotal.py

You should see:

.. code-block:: text

   Success(12.5)
   Failure(ValueError('unit_price must not be negative'))

``json.loads`` converts the JSON string to a Python dictionary. The function
returns ``Success`` for an accepted price and ``Failure`` for an expected input
error instead of raising it to the caller.

The ``Exception`` type argument accommodates every exception type caught by
the function. See the :doc:`../reference/api/types` for complete ``Result``
details.

Step 2: Parse an Order Quantity
-------------------------------

Remove the two ``print`` lines. Add this function and the new calls at the
bottom of ``order_subtotal.py``:

.. code-block:: python

   def parse_quantity(order_json: str) -> Result[Exception, int]:
       """Read and validate an order quantity."""
       try:
           quantity = int(json.loads(order_json)["quantity"])
           if quantity <= 0:
               raise ValueError("quantity must be greater than zero")
           return Result[Exception, int].Success(quantity)
       except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
           return Result[Exception, int].Failure(error)

   print(parse_quantity('{"quantity": 4}'))
   print(parse_quantity('{"quantity": 0}'))

Run the file:

.. code-block:: bash

   python order_subtotal.py

You should see:

.. code-block:: text

   Success(4)
   Failure(ValueError('quantity must be greater than zero'))

The quantity parser follows the same pattern as the price parser. It returns
the validated integer or preserves the input error inside ``Failure``.

Step 3: Calculate a Subtotal
----------------------------

Remove the two ``print`` lines. Add this function and call at the bottom of
``order_subtotal.py``:

.. code-block:: python

   def calculate_subtotal(unit_price: float, quantity: int) -> float:
       return unit_price * quantity

   print(calculate_subtotal(12.50, 4))

Run the file:

.. code-block:: bash

   python order_subtotal.py

You should see:

.. code-block:: text

   50.0

``calculate_subtotal`` accepts plain validated values. The next step will
provide those values from the two ``Result``-returning parsers.

Step 4: Combine the Parsing Steps
---------------------------------

Replace the contents of ``order_subtotal.py`` with the complete program:

.. code-block:: python

   import json

   from katharos.syntax_sugar import DoBlock, do
   from katharos.types import Result


   def parse_unit_price(product_json: str) -> Result[Exception, float]:
       """Read and validate a product's unit price."""
       try:
           unit_price = float(json.loads(product_json)["unit_price"])
           if unit_price < 0:
               raise ValueError("unit_price must not be negative")
           return Result[Exception, float].Success(unit_price)
       except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
           return Result[Exception, float].Failure(error)


   def parse_quantity(order_json: str) -> Result[Exception, int]:
       """Read and validate an order quantity."""
       try:
           quantity = int(json.loads(order_json)["quantity"])
           if quantity <= 0:
               raise ValueError("quantity must be greater than zero")
           return Result[Exception, int].Success(quantity)
       except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
           return Result[Exception, int].Failure(error)


   def calculate_subtotal(unit_price: float, quantity: int) -> float:
       return unit_price * quantity


   @do(Result)
   def order_subtotal(
       product_json: str,
       order_json: str,
   ) -> DoBlock[Result, float]:
       unit_price: float = yield parse_unit_price(product_json)
       quantity: int = yield parse_quantity(order_json)
       return calculate_subtotal(unit_price, quantity)


   print(order_subtotal('{"unit_price": 12.50}', '{"quantity": 4}'))
   print(order_subtotal('{"unit_price": 12.50}', '{"quantity": 0}'))

Run the completed program:

.. code-block:: bash

   python order_subtotal.py

You should see:

.. code-block:: text

   Success(50.0)
   Failure(ValueError('quantity must be greater than zero'))

Each ``yield`` provides a plain validated value. If either parser returns a
``Failure``, the function stops before calculating the subtotal. A successful
subtotal is lifted into ``Success`` automatically.

What You Built
--------------

You built an order-subtotal calculator that:

- Parses JSON input and captures expected input errors in ``Failure``.
- Represents validated prices and quantities with ``Success``.
- Keeps the subtotal calculation independent from parsing and validation.
- Combines dependent ``Result`` values with ``@do(Result)``.
- Stops at the first parsing or validation failure.

Next Steps
----------

- Continue with :doc:`immutable-lists` to work with immutable collections.
- See :doc:`../how-to/catch-exceptions` to replace manual ``try`` and ``except``
  blocks with ``Result.catch``.
- Read :doc:`../explanation/error-handling-and-tracebacks` to understand why
  Katharos represents expected failures as values.
- Consult the :doc:`../reference/api/types` for the complete ``Result`` API.
