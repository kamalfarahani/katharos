Getting Started with Katharos
==============================

Prerequisites
-------------

- Python 3.13 or later
- pip package manager

Step 1: Install Katharos
------------------------

In this tutorial, we will install Katharos and verify it works. First, install Katharos using pip:

.. code-block:: bash

   pip install katharos

Or using uv:

.. code-block:: bash

   uv add katharos

Step 2: Verify Your Installation
---------------------------------

Now, create a new Python file called ``verify_katharos.py``:

.. code-block:: python

   import katharos
   from katharos.types import Maybe

   print("Katharos installed successfully!")
Run the file:

.. code-block:: bash

   python verify_katharos.py

You should see output like this:

.. code-block:: text

   Katharos installed successfully!

