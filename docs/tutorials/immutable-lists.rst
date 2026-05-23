Working with Immutable Lists
============================

In this tutorial, we will build a product inventory system using ``ImmutableList`` and ``NonEmptyList``. Along the way, we will encounter ``fmap``, list concatenation, monadic bind, and the safety guarantee that immutable collections are never modified in place.

Prerequisites
-------------

- Python 3.13 or later
- Katharos installed (see :doc:`getting-started`)
- Complete the :doc:`functor` tutorial so you are familiar with ``fmap``

Step 1: Create Your First Immutable List
-----------------------------------------

Create a new file called ``inventory.py`` with the following contents:

.. code-block:: python

   from katharos.types import ImmutableList

   prices = ImmutableList([19.99, 99.99, 699.99])

   print(len(prices))
   print(prices[0])
   print(list(prices))

Run the file:

.. code-block:: bash

   python inventory.py

You should see:

.. code-block:: text

   3
   19.99
   [19.99, 99.99, 699.99]

Notice that you can read elements by index and convert to a plain list, but the list itself cannot be modified in place.

Step 2: Work with Product Data
-------------------------------

Now we will create a realistic product inventory. Replace the contents of ``inventory.py`` with:

.. code-block:: python

   from katharos.types import ImmutableList
   from dataclasses import dataclass

   @dataclass(frozen=True)
   class Product:
       name: str
       price: float
       category: str

   products = ImmutableList([
       Product("Book", 19.99, "books"),
       Product("Laptop", 999.99, "electronics"),
       Product("Phone", 699.99, "electronics"),
   ])

   print(f"Total products: {len(products)}")
   print(f"First product: {products[0].name}")

Run the file:

.. code-block:: bash

   python inventory.py

You should see:

.. code-block:: text

   Total products: 3
   First product: Book

Step 3: Transform Data with fmap
---------------------------------

Now we will extract prices and names from the product list. Add this code at the bottom of ``inventory.py``:

.. code-block:: python

   prices = products.fmap(lambda p: p.price)
   print(prices)

   names = products.fmap(lambda p: p.name)
   print(names)

Run the file. The new lines at the bottom should be:

.. code-block:: text

   ImmutableList([19.99, 999.99, 699.99])
   ImmutableList(['Book', 'Laptop', 'Phone'])

Notice that ``fmap`` creates a new list without modifying the original ``products`` list.

Step 4: Combine Lists with Concatenation
-----------------------------------------

Now we will add more products to our inventory. Add this code at the bottom of ``inventory.py``:

.. code-block:: python

   new_products = ImmutableList([
       Product("Tablet", 399.99, "electronics"),
       Product("Pen", 2.99, "stationery"),
   ])

   all_products = products + new_products
   print(len(all_products))
   print(len(products))

Run the file. The new lines should be:

.. code-block:: text

   5
   3

Notice that ``products`` still has 3 items. Concatenation produced a new list; it did not modify either of the originals.

Step 5: Filter Products with bind
-----------------------------------

We will now filter products by category. Add this code at the bottom of ``inventory.py``:

.. code-block:: python

   def get_electronics(product: Product) -> ImmutableList[Product]:
       if product.category == "electronics":
           return ImmutableList([product])
       return ImmutableList([])

   electronics = products.bind(get_electronics)
   print([p.name for p in electronics])

Run the file. The new line should be:

.. code-block:: text

   ['Laptop', 'Phone']

Notice how ``bind`` works: it applies ``get_electronics`` to every element and flattens the results. Elements that return an empty list are effectively removed.

Step 6: Use Lists as Dictionary Keys
--------------------------------------

Because ``ImmutableList`` is hashable, it can be used as a dictionary key. Add this code at the bottom of ``inventory.py``:

.. code-block:: python

   cache: dict[ImmutableList[str], float] = {}

   electronics_names = ImmutableList(["Laptop", "Phone"])
   cache[electronics_names] = 1699.98

   total = cache[electronics_names]
   print(f"Cached total: {total}")

Run the file. The new line should be:

.. code-block:: text

   Cached total: 1699.98

A plain Python ``list`` cannot be used as a dictionary key because it is mutable. ``ImmutableList`` can because it guarantees the contents never change.

Step 7: Guarantee Non-Empty Lists with NonEmptyList
-----------------------------------------------------

When you need to ensure a list always has at least one element, use ``NonEmptyList``. Add this code at the bottom of ``inventory.py``:

.. code-block:: python

   from katharos.types import NonEmptyList

   electronics_nel = NonEmptyList(
       Product("Laptop", 999.99, "electronics"),
       [
           Product("Phone", 699.99, "electronics"),
           Product("Tablet", 399.99, "electronics"),
       ]
   )

   print(electronics_nel.head)
   total = electronics_nel.head.price + sum(p.price for p in electronics_nel.tail)
   print(f"Total: {total}")

Run the file. The new lines should be:

.. code-block:: text

   Product(name='Laptop', price=999.99, category='electronics')
   Total: 2099.97

Notice that you can access ``.head`` without checking whether the list is empty, because ``NonEmptyList`` enforces the non-empty invariant at construction time.

What We Built
-------------

We built a product inventory system that stores products in an ``ImmutableList``, transforms and filters them with ``fmap`` and ``bind``, combines lists without mutation, uses an ``ImmutableList`` as a cache key, and enforces a non-empty invariant with ``NonEmptyList``.
