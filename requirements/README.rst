Requirements/dependencies
=========================

These directories specify the Python (and system) dependencies for the LMS and Studio.

- ``edx`` contains the normal Python requirements files
- ``edx-sandbox`` contains the requirements files for Codejail
- ``constraints.txt`` is shared between the two

(In a normal `OEP-18`_-compliant repository, the ``*.in`` and ``*.txt`` files would be
directly in the requirements directory.)

.. _OEP-18: https://github.com/openedx/open-edx-proposals/blob/master/oeps/oep-0018-bp-python-dependencies.rst

Upgrading/downgrading just one dependency
-----------------------------------------

Want to upgrade just *one* dependency without pulling in other upgrades? Here's how:

1. Change your dependency to a minimum-version constraint, e.g. ``my-dep>=1.2.3`` (or update the constraint if it already exists)
2. Run ``make compile-requirements`` to recompute dependencies with this new constraint

If you instead need to surgically *downgrade* a dependency, perhaps in order to revert a change which broke things:

1. Add an exact-match or max-version constraint to ``constraints.txt`` with a comment explaining why (and ideally a ticket or issue link)
2. Lower the minimum-version constraint, if it exists

    - Not sure if there is one? Try going on to the next step and seeing if it complains!

3. Run ``make compile-requirements``

This is considerably safer than trying to manually edit the ``*.txt`` files, which can easily result in incompatible dependency versions.
