.. _operations:

Operations
==========

Static assets
-------------

.. DOCUMENTME

.. autofunction:: pavelib.assets.webpack

Database management
-------------------

.. DOCUMENTME

Full reset
~~~~~~~~~~

It is possible to completely reset the database by running::
    
    ./manage.py lms reset_db

.. automodule:: openedx.core.djangoapps.util.management.commands.reset_db

Documentation
-------------

Reference documentation
~~~~~~~~~~~~~~~~~~~~~~~

To generate the reference documentation (i.e: these docs), run::
    
    make reference-docs

The generated html files are then available in the ``edx-platform/docs/reference/_build/html`` folder. To view them, run::
    
    cd docs/reference/_build/html
    python3 -m http.server 8008
    # Then open http://localhost:8008 in your browser