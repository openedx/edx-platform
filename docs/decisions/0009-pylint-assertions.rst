Pylint Assertions Standardization
---------------------------------

Status
======

Proposed

Context
=======

The edx-platform test suite includes a massive number of individual assertions, written over time for different Python versions and test runners.  A nontrivial number of these currently trigger deprecation warnings, as they are slated for replacement or removal in future Python versions.  A very high percentage of them use assertion methods from Python's ``unittest`` module, which were inspired by Java's jUnit library long ago and have notable drawbacks vs. the `assert statement rewriting`_ built into our current test runner, pytest.  In particular:

* ``assert`` statements are typically shorter and easier to read.  For example:

  * ``self.assertNotIn("session_key", self.client.session)`` (unittest) becomes

  * ``assert "session_key" not in self.client.session`` (pytest)

* The output of failed pytest-rewritten assertions is often more helpful than their ``unittest`` equivalents.

* Using ``assert`` eliminates the need to remember which of 20+ methods is most appropriate for your current assertion, or to look up the correct order of arguments for the one you choose.

* The ``unittest`` assertions don't follow standard Python naming conventions (because they were adopted verbatim from a Java library).

.. _assert statement rewriting: https://docs.pytest.org/en/stable/assert.html

We want to fix at least the deprecation warnings, and feel that we'd also benefit from a more comprehensive switch to pytest assertions if it's easy enough to implement.

Decisions
=========

1. We will use `codemod-unittest-to-pytest-asserts`_ to refactor essentially all of the ``unittest.TestCase`` assertion methods in edx-platform to use the ``assert`` statement instead.  This pre-existing tool essentially does what we want, and so far has only needed one patch to resolve a corner case problem we encountered while trying it out.  This will be done in multiple PRs to simplify code review and minimize merge conflicts.

2. We recommend ``assert`` statements for most new test assertions (other than specialized assertion methods provided by ``unittest.mock``, Django's ``TestCase`` subclass, etc.)

3. If the edx-platform assertion refactoring goes well and developers are satisfied with the results, we will recommend (but not require) that owners of other repositories perform a similar refactoring.

4. We will time-box an effort to create a custom pylint check to catch new usage of the replaced ``unittest`` assertion methods.

.. _codemod-unittest-to-pytest-asserts: https://github.com/hanswilw/codemod-unittest-to-pytest-asserts

Consequences
============

* Most usage of assertion methods from ``unittest.TestCase`` in edx-platform will switch to using the ``assert`` statement.  Usage of assertion methods from ``unittest.mock``, ``django.test.TestCase``, etc. will stay as is.

* The number of deprecation warnings in edx-platform will decrease, simplifying future Python upgrades.

* We will get slightly better diagnostic information for many types of test failures.
