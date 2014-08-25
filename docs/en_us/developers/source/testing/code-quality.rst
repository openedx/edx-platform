************
Code Quality
************

In order to keep our code as clear and readable as possible, we use various
tools to assess the quality of pull requests:

* We use the `pep8`_ tool to follow `PEP-8`_ guidelines
* We use `pylint`_ for static analysis and uncovering trouble spots in our code

Our codebase is far from perfect, but the goal is to steadily improve our quality
over time. To do this, we wrote a tool called `diff-quality`_ that will
only report on the quality violations on lines that have changed in a
pull request. Using this tool, we can ensure that pull requests do not introduce
any new quality violations -- and ideally, they clean up existing violations
in the process of introducing other changes.

To check the quality of your pull request, just go to the top level of the
edx-platform codebase and run::

    $ paver run_quality

You can also use the `paver run_pep8`` and ``paver run_pylint`` commands to run just pep8 or
pylint.

This will print a report of the quality violations that your branch has made.

Although we try to be vigilant and resolve all quality violations, some Pylint
violations are just too challenging to resolve, so we opt to ignore them via
use of a pragma. A pragma tells Pylint to ignore the violation in the given
line. An example is::

    self.assertEquals(msg, form._errors['course_id'][0])  # pylint: disable=protected-access

The pragma starts with a ``#`` two spaces after the end of the line. We prefer
that you use the full name of the error (``pylint: disable=unused-argument`` as
opposed to ``pylint: disable=W0613``), so it's more clear what you're disabling
in the line.

.. _PEP-8: http://legacy.python.org/dev/peps/pep-0008/
.. _pep8: https://pypi.python.org/pypi/pep8
.. _coverage.py: https://pypi.python.org/pypi/coverage
.. _pylint: http://pylint.org/
.. _diff-quality: https://github.com/edx/diff-cover
