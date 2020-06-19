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
* In the future, the alternative would be to add a migration that adds an active (True) waffle flag database record if a record doesn't already exist.

  * If the record already exists, do not replace it whether or not it is active. Its value is already represented in the database and may have been set via admin.

Consequences
============

* We will need to add the appropriate migrations for each flag currently using ``flag_undefined_default=True``, and then finally remove the deprecated ``flag_undefined_default`` argument.

Rejected Alternatives
=====================

We are clearly rejecting the ``flag_undefined_default`` argument.

We are also rejecting any other alternative that would separate this default from the normal usage of the waffle flag record.
