Requirements/dependencies
=========================

These directories specify the Python (and system) dependencies for the LMS and Studio.

- ``edx`` contains the normal Python requirements files
- ``edx-sandbox`` contains the requirements files for Codejail
- ``constraints.txt`` is shared between the two

(In a normal `OEP-18`_-compliant repository, the ``*.in`` and ``*.txt`` files would be
directly in the requirements directory.)

.. _OEP-18: https://github.com/openedx/open-edx-proposals/blob/master/oeps/oep-0018-bp-python-dependencies.rst

Upgrading just one dependency
-----------------------------

Want to upgrade just *one* dependency without pulling in other upgrades? You can `run the upgrade-one-python-dependency.yml workflow <https://github.com/openedx/edx-platform/actions/workflows/upgrade-one-python-dependency.yml>`_ to have a pull request made against a branch of your choice.

Or, if you need to do it locally, you can use the ``upgrade-package`` make target directly. For example, you could run ``make upgrade-package package=ecommerce``. But the GitHub workflow is likely easier.

Downgrading a dependency
------------------------

If you instead need to surgically *downgrade* a dependency:

1. Add an exact-match or max-version constraint to ``constraints.txt`` with a comment explaining why (and ideally a ticket or issue link). Here's what it might look like::

     # frobulator 2.x has breaking API changes; see https://github.com/openedx/edx-platform/issue/1234567 for fixing it
     frobulator<2.0.0

2. Run ``make compile-requirements``

This is considerably safer than trying to manually edit the ``*.txt`` files, which can easily result in incompatible dependency versions.
