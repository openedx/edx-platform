Running a Single Test
~~~~~~~~~~~~~~~~~~~~~

various ways to run tests using pytest::

    pytest test_m­od.py                          # Run tests in a module.
    pytest testing/                             # Run tests in a directory.
    pytest test_m­od.p­y:­:te­st_func               # Run a specific test within a module.
    pytest test_m­od.p­y:­:Te­stC­las­s               # Run tests in a class
    pytest test_m­od.p­y:­:Te­stC­las­s::­tes­t_m­ethod  # Run a specific method of a class.

For example, this command runs a single python unit test file::

    pytest common/lib/xmodule/xmodule/tests/test_stringify.py


To select tests to run based on their name, provide an expression to the
`pytest -k option`_ which performs a substring match on test names::

    pytest common/lib/xmodule/xmodule/tests/test_stringify.py -k test_stringify

.. _pytest -k option: https://docs.pytest.org/en/latest/example/markers.html#using-k-expr-to-select-tests-based-on-their-name
.. _node ID: https://docs.pytest.org/en/latest/example/markers.html#node-id

Alternatively, you can select tests based on their `node ID`_ directly,
which is useful when you need to run only one of mutliple tests with the same
name in different classes or files.

This command runs any python unit test method that matches the substring
`test_stringify` within a specified TestCase class within a specified file::

    pytest common/lib/xmodule/xmodule/tests/test_stringify.py::TestCase -k test_stringify

Note: if the method has an `@ddt.data` decorator, ddt will create multiple
methods with the same prefix name and each individual data input as the suffix
(e.g. `test_stringify_1_foo`). To test all of the ddt.data variations of the
same test method, pass the prefix name to the pytest `-k` option.

If you need to run only one of the test variations, you can the get the
name of all test methods in a class, file, or project, including all ddt.data
variations, by running pytest with `--collectonly`::

    pytest common/lib/xmodule/xmodule/tests/test_stringify.py --collectonly


This is an example of how to run a single test and get stdout shown immediately, with proper env config::

    pytest cms/djangoapps/contentstore/tests/test_import.py -s

How to output coverage locally