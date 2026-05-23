Getting Started with Katharos
==============================

In this tutorial, we will install Katharos and write our first program using the ``Maybe`` type. Along the way, we will verify the installation works and confirm we can import from the library.

Prerequisites
-------------

- Python 3.13 or later
- pip package manager

Step 1: Install Katharos
------------------------

Install Katharos using pip:

.. code-block:: bash

   pip install katharos

You will see pip download and install the package. The last line of output should say something like ``Successfully installed katharos-...``.

Step 2: Verify Your Installation
---------------------------------

Create a new Python file called ``verify_katharos.py``:

.. code-block:: python

   import katharos
   from katharos.types import Maybe

   print("Katharos installed successfully!")

Run the file:

.. code-block:: bash

   python verify_katharos.py

You should see:

.. code-block:: text

   Katharos installed successfully!

If you see an ``ImportError`` instead, the installation did not complete successfully — re-run the pip install step and check for any error messages.

What We Built
-------------

We installed Katharos and confirmed the library can be imported. In the next tutorial, we will use the ``Maybe`` type to safely handle values that might be missing.
