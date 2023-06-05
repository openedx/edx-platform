Refactor Waffle Flag Default
****************************

Status
======

Accepted

Context
=======

While working on the toggle reports, it became clear that the value for WaffleFlags (and derivatives like CourseWaffleFlag) in all environments was difficult to determine, and difficult to reason about.

By default, the original waffle flag values are False, unless a record is created to turn it on under certain circumstances. Having the ability to make the default True in code was confusing when looking in Admin and trying to determine the current value of the flag. It also would have been complex to have the report have to investigate code to try to determine this value.

Decision
========

* Retire the ``flag_undefined_default`` argument for WaffleFlag and CourseWaffleFlag that allowed you to change the default to True in code.
* Do not introduce any new ability to adjust the default in code.
* Teams can use any of the following alternatives instead:

  * The flag can simply be removed at this time if it was meant to be temporary.
  * The flag could be replaced with a Django Setting, if the features of a flag are not needed for the permanent toggle.
  * You could add a migration that adds an active (True) waffle flag database record if a record doesn't already exist.
  * You could introduce and replace an *enable* flag with a new *disable* flag. This might be useful when a permanent toggle is desired that requires features of a waffle flag, and where disabling would now be the exceptional case, since the default would be inactive (False).

Consequences
============

* We will need to implement one of the alternate solutions for each flag currently using ``flag_undefined_default=True``, and then finally remove the deprecated ``flag_undefined_default`` argument.

UPDATE: This work has been completed and ``flag_undefined_default`` has been removed.

Rejected Alternatives
=====================

We are clearly rejecting the ``flag_undefined_default`` argument.

We are also rejecting any other alternative that would separate this default from the normal usage of the waffle flag record.
