Running a Single Test
~~~~~~~~~~~~~~~~~~~~~

Various ways to run tests using pytest::

    pytest path/test_m­od.py                          # Run tests in a module.
    pytest path/test_m­od.p­y:­:te­st_func               # Run a specific test within a module.
    pytest path/test_m­od.p­y:­:Te­stC­las­s               # Run tests in a class
    pytest path/test_m­od.p­y:­:Te­stC­las­s::­tes­t_m­ethod  # Run a specific method of a class.
    pytest path/testing/                             # Run tests in a directory.

For example, this command runs a single python unit test file::

    pytest common/lib/xmodule/xmodule/tests/test_stringify.py

Various tools like ddt create tests with very complex names, rather than figuring out the name yourself, you can:

To select tests to run based on their name, provide an expression to the `pytest -k option`_ which performs a substring match on test names::

    pytest common/lib/xmodule/xmodule/tests/test_stringify.py -k test_stringify

.. _pytest -k option: https://docs.pytest.org/en/latest/example/markers.html#using-k-expr-to-select-tests-based-on-their-name
.. _node ID: https://docs.pytest.org/en/latest/example/markers.html#node-id


Alternatively, you can the get the name of all test methods in a class, file, or project, including all ddt.data variations, by running pytest with `--collectonly`::

    pytest common/lib/xmodule/xmodule/tests/test_stringify.py --collectonly
