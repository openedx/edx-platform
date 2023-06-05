Leave CourseWaffleFlag
**********************

Status
======

Accepted

Context
=======

It was decided in 0002-waffle-utils-extraction to remove waffle_utils to the shared library edx-toggles.  However, moving the class CourseWaffleFlag would be complicated due to its model data, and it is unclear how much usage it would get in other IDAs.

Decision
========

It has been decided to leave CourseWaffleFlag inside edx-platform for the time being, and to delay its extraction until the work seems warranted (i.e. another IDA actually wants to make use of it).

Consequences
============

* The toggle state endpoint will need to be updated to allow WaffleFlag subclasses to add state data.

Rejected Alternative
====================

The alternative would be to extract CourseWaffleFlag to the shared library.  As noted, this can be decided in the future. If extraction were to be pursued, some things to consider would be:

* Ensuring course override data is properly migrated from the old to new method of defining course overrides. It is possible that this migration would need to be documented and maintained for the Open edX release as well.
* Given the data migration needed, it might be practical to migrate course override data from a ConfigurationModel to a Django Setting (using remote config) before extraction.
* The toggle state report uses the term `course_id` for the course overrides, but this is actually a `course_run_id` in the context of other IDAs. Will its name be configurable per IDA?
