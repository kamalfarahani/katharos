Working with Immutable Lists
====================================

In this tutorial, you'll learn how to build a product inventory system using immutable lists. By the end, you'll understand how to safely work with collections that can't be accidentally modified, and how to use functional operations to transform and combine them.

What You'll Build
-----------------

A simple product inventory system that:

- Stores a list of products that cannot be accidentally modified
- Filters products by category
- Calculates totals and statistics
- Uses lists as dictionary keys for caching results

Let's Start: Create Your First Immutable List
----------------------------------------------

First, import and create an immutable list:

.. code-block:: python

   from katharos.types import ImmutableList

   # Create a list of product prices
   prices = ImmutableList([19.99, 99.99, 699.99])
   
   print(len(prices))        # 3
   print(prices[0])          # 19.99
   print(list(prices))       # [19.99, 99.99, 699.99]

Try it yourself: Create an immutable list with your own numbers and access elements by index.

Step 1: Work with Product Data
-------------------------------

Let's create a more realistic inventory with product objects:

.. code-block:: python

   from katharos.types import ImmutableList
   from dataclasses import dataclass

   @dataclass(frozen=True)
   class Product:
       name: str
       price: float
       category: str

   # Create an immutable product list
   products = ImmutableList([
       Product("Book", 19.99, "books"),
       Product("Laptop", 999.99, "electronics"),
       Product("Phone", 699.99, "electronics"),
   ])

   print(f"Total products: {len(products)}")
   print(f"First product: {products[0].name}")

Step 2: Transform Data with fmap
--------------------------------

Now let's extract prices from products using ``fmap``:

.. code-block:: python

   # Extract all prices
   prices = products.fmap(lambda p: p.price)
   print(prices)  # ImmutableList([19.99, 999.99, 699.99])

   # Get all product names
   names = products.fmap(lambda p: p.name)
   print(names)  # ImmutableList(['Book', 'Laptop', 'Phone'])

The key insight: ``fmap`` creates a new list without modifying the original. This is safe and predictable.

Step 3: Combine Lists with Concatenation
-----------------------------------------

Let's add more products to our inventory:

.. code-block:: python

   new_products = ImmutableList([
       Product("Tablet", 399.99, "electronics"),
       Product("Pen", 2.99, "stationery"),
   ])

   # Combine the lists
   all_products = products + new_products
   print(len(all_products))  # 5

   # Original lists are unchanged
   print(len(products))      # 3
   print(len(new_products))  # 2

Step 4: Chain Operations with bind
----------------------------------

Now let's find all products in a category and create a discount list for each:

.. code-block:: python

   def create_discounts(product: Product) -> ImmutableList[tuple[str, float]]:
       """For each product, return a list of (name, discounted_price) tuples."""
       return ImmutableList([
           (product.name, product.price * 0.9),  # 10% off
           (product.name, product.price * 0.8),  # 20% off
       ])

   # Chain the operation
   discounts = products.bind(create_discounts)
   print(discounts)
   # ImmutableList([
   #   ('Book', 17.99), ('Book', 15.99),
   #   ('Laptop', 899.99), ('Laptop', 799.99),
   #   ('Phone', 629.99), ('Phone', 559.99)
   # ])

Step 5: Use Lists as Dictionary Keys
-------------------------------------

Because immutable lists are hashable, you can use them as dictionary keys for caching:

.. code-block:: python

   # Create a cache mapping product lists to results
   cache: dict[ImmutableList[str], float] = {}

   # Use a product name list as a key
   electronics_names = ImmutableList(["Laptop", "Phone"])
   cache[electronics_names] = 1699.98  # Total price

   # Retrieve from cache
   total = cache[electronics_names]
   print(f"Cached total: {total}")

Step 6: Guarantee Non-Empty Lists with NonEmptyList
----------------------------------------------------

When you need to ensure a list always has at least one element, use ``NonEmptyList``:

.. code-block:: python

   from katharos.types import NonEmptyList

   # Create a non-empty list (head + optional tail)
   electronics = NonEmptyList(
       Product("Laptop", 999.99, "electronics"),
       [
           Product("Phone", 699.99, "electronics"),
           Product("Tablet", 399.99, "electronics"),
       ]
   )

   # Access head and tail safely
   print(electronics.head)  # Product(name='Laptop', ...)
   print(electronics.tail)  # [Product(...), Product(...)]

   # Calculate total safely without checking if list is empty
   total = electronics.head.price + sum(p.price for p in electronics.tail)
   print(f"Total: {total}")  # 2099.97

Step 7: Build a Complete Inventory System
------------------------------------------

Let's combine everything into a practical inventory system:

.. code-block:: python

   from katharos.types import ImmutableList, NonEmptyList
   from dataclasses import dataclass

   @dataclass(frozen=True)
   class Product:
       name: str
       price: float
       category: str

   # Initialize inventory
   products = ImmutableList([
       Product("Book", 19.99, "books"),
       Product("Laptop", 999.99, "electronics"),
       Product("Phone", 699.99, "electronics"),
       Product("Tablet", 399.99, "electronics"),
   ])

   # Filter by category using bind
   def get_category_products(category: str) -> ImmutableList[Product]:
       return products.bind(
           lambda p: ImmutableList([p]) if p.category == category else ImmutableList([])
       )

   electronics = get_category_products("electronics")
   print(f"Electronics: {[p.name for p in electronics]}")

   # Calculate statistics
   prices = electronics.fmap(lambda p: p.price)
   if len(prices) > 0:
       nel = NonEmptyList(prices[0], list(prices[1:]))
       total = nel.head + sum(nel.tail)
       average = total / len(prices)
       print(f"Total: ${total:.2f}, Average: ${average:.2f}")

   # Cache results by product list
   cache: dict[ImmutableList[Product], dict] = {
       electronics: {
           "total": total,
           "average": average,
           "count": len(electronics),
       }
   }

   # Retrieve cached results
   stats = cache[electronics]
   print(f"Cached stats: {stats}")

Next Steps
----------

Now that you understand the basics, explore the reference documentation to learn about:

- All available operations on ``ImmutableList`` and ``NonEmptyList``
- Type covariance and how it affects your code
- The monoid interface for combining lists
- The applicative interface for advanced transformations
