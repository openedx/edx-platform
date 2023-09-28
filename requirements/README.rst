Requirements/dependencies
#########################

These directories specify the Python (and system) dependencies for the LMS and Studio.

- ``edx`` contains the normal Python requirements files
- ``edx-sandbox`` contains the requirements files for Codejail
- ``constraints.txt`` is shared between the two

(In a normal `OEP-18`_-compliant repository, the ``*.in`` and ``*.txt`` files would be
directly in the requirements directory.)

.. _OEP-18: https://github.com/openedx/open-edx-proposals/blob/master/oeps/oep-0018-bp-python-dependencies.rst

While the ``*.in`` files are intended to be updated manually, the ``*.txt`` files should only be manipulated using Makefile targets in a Linux environment (to match our build and deploy systems). For developers on Mac, this can be achieved by using the GitHub workflows or by running Make targets from inside devstack's lms-shell or another Linux environment.

If you don't have write permissions to openedx/edx-platform, you'll need to run these workflows on a fork.

Workflows and Makefile targets
******************************

Add a dependency
================

To add a Python dependency, specify it in the appropriate ``requirements/edx/*.in`` file, push that up to a branch, and then use the `compile-python-requirements.yml workflow <https://github.com/openedx/edx-platform/actions/workflows/compile-python-requirements.yml>`_ to run ``make compile-requirements`` against your branch. This will ensure the lockfiles are updated with any transitive dependencies and will ping you on a PR for updating your branch.

Upgrade just one dependency
===========================

Want to upgrade just *one* dependency without pulling in other upgrades? You can `run the upgrade-one-python-dependency.yml workflow <https://github.com/openedx/edx-platform/actions/workflows/upgrade-one-python-dependency.yml>`_ to have a pull request made against a branch of your choice.

Or, if you need to do it locally, you can use the ``upgrade-package`` make target directly. For example, you could run ``make upgrade-package package=ecommerce``.

If your dependency is pinned in constraints.txt, you'll need to enter an explicit version number in the appropriate field when running the workflow; this will include an update to the constraint file in the resulting PR.

Downgrade a dependency
======================

If you instead need to surgically *downgrade* a dependency:

1. Add an exact-match or max-version constraint to ``constraints.txt`` with a comment explaining why (and ideally a ticket or issue link). Here's what it might look like::

     # frobulator 2.x has breaking API changes; see https://github.com/openedx/edx-platform/issue/1234567 for fixing it
     frobulator<2.0.0

2. After pushing that up to a branch, use the `compile-python-requirements.yml workflow <https://github.com/openedx/edx-platform/actions/workflows/compile-python-requirements.yml>`_ to run ``make compile-requirements`` against your branch.

Upgrade all dependencies
========================

 You can use the `upgrade-requirements Github Workflow <https://github.com/openedx/edx-platform/actions/workflows/upgrade-python-requirements.yml>`_ to make a PR that upgrades as many packages as possible to newer versions. This is a wrapper around ``make upgrade`` and is run on a schedule to keep dependencies up to date.

Inconsistent dependencies
*************************

You might be directed to this section if a PR check for consistent dependencies has failed.

Did you run ``make upgrade`` or ``make compile-requirements`` on a Mac directly?
================================================================================

Some packages have different dependencies on Mac vs. Linux. Usually this is not relevant in production (they generally have to do with desktop integrations of developer tools) but this does cause "churn" and make it harder to review PRs when dependencies are alternatingly recompiled on Mac and Linux. As edx-platform runs on Linux, we want to ensure that dependencies are compiled for that platform.

Solutions for Mac users:

- Use the workflow described in `Upgrading just one dependency`_.
- You can run ``make lms-shell`` in devstack to get a Linux environment for more complicated operations.

Did you hand-edit the .txt files?
=================================

Hand-editing the .txt requirements files often leads to dependency conflicts, failed deployments, or outages. It's easy to forget to update all the locations where a requirement appears, and it's often not feasible to track down all of the transitive dependencies of the package you want to upgrade.

Luckily, we have simple runbooks for upgrading or downgrading a single package, which are the most common cases:

- `Upgrading just one dependency`_
- `Downgrading a dependency`_

Is there an unpinned git dependency?
====================================

If the diff relates to a dependency that is installed from git rather than from PyPI (such as being a transitive dependency of anything in github.in), check whether any of the dependencies in github.in has failed to pin a specific commit. We want to have as few of these dependencies as possible, as they're a maintenance and performance problem, and there are important instructions at the top of that file for how to manage them.

Help, I didn't change any dependencies, and this is still failing!
==================================================================

It's possible that someone introduced an inconsistency on the master branch, in which case please submit a new PR off of master after running ``make compile-requirements`` (but see notes above for Mac users). Or perhaps your branch was made while there was such an inconsistency, in which case please rebase onto master or merge down from master to your branch.
