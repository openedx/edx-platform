Requirements/dependencies
=========================

These directories specify the Python (and system) dependencies for the LMS and Studio.

- ``edx`` contains the normal Python requirements files
- ``edx-sandbox`` contains the requirements files for Codejail
- ``constraints.txt`` is shared between the two

(In a normal `OEP-18`_-compliant repository, the ``*.in`` and ``*.txt`` files would be
directly in the requirements directory.)

.. _OEP-18: https://github.com/edx/open-edx-proposals/blob/master/oeps/oep-0018-bp-python-dependencies.rst

Upgrading just one dependency
-----------------------------

Want to upgrade/downgrade just *one* dependency without pulling in other upgrades? Here's how:

1. Add ``my-dep==1.2.3`` to ``requirements/constraints.txt`` temporarily (pin the specific version you want to upgrade to)
2. Run ``make compile-requirements`` to recompute dependencies with this new constraint
3. Remove your constraint

The resulting changes can then be committed.

This is particularly useful when you need to downgrade a dependency which brought in a bug but don't want to roll back all dependency changes. It's also considerably safer than trying to manually edit the ``*.txt`` files, which can easily result in incompatible dependency versions.
