*************
Code Coverage
*************

We measure which lines of our codebase are covered by unit tests using
`coverage.py`_ for Python and `JSCover`_ for Javascript.

Our codebase is far from perfect, but the goal is to steadily improve our coverage
over time. To do this, we wrote a tool called `diff-cover`_ that will
report which lines in your branch are not covered by tests, while ignoring
other lines in the project that may not be covered. Using this tool,
we can ensure that pull requests have a very high percentage of test coverage
-- and ideally, they increase the test coverage of existing code, as well.

To check the coverage of your pull request, just go to the top level of the
edx-platform codebase and run::

    $ paver coverage

This will print a coverage report for your branch. We aim for
a coverage report score of 95% or higher. We also encourage you to write
acceptance tests as your changes require.

.. _coverage.py: https://pypi.python.org/pypi/coverage
.. _JSCover: http://tntim96.github.io/JSCover/
.. _diff-cover: https://github.com/edx/diff-cover
