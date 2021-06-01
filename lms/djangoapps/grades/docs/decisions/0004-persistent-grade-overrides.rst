Persistent Subsection Grade Overrides
-------------------------------------

New decisions have been made about subsection grade overrides, see 0006-overrides-applied-separately_.

.. _0006-overrides-applied-separately: 0006-overrides-applied-separately.rst

Status
======

Accepted (circa Summer 2017)

Superseded (January 2019)

Context
=======

It is sometimes necessary to override a learner's score for an entire subsection/assignment.
For example, for a graded and proctored exam, we may wish to automatically fail a learner's
attempt on the exam with a score of zero if the proctor indicates suspicious behavior
on the part of the learner.

Decisions
=========

* We want to allow for the automatic or manual creation of overrides at the subsection-level.
* We'll create a class called ``PersistentSubsectionGradeOverride`` to store the overridden scores, and
  an instance of this class will always be associated with an instance of ``PersistentSubsectionGrade``.
* When updating a ``PersistentSubsectionGrade``, we'll persist the overridden scores from an associated
  ``PersistentSubsectionGradeOverride`` (if one exists) instead of the computed value for the subsection grade.
* No more than one ``PersistentSubsectionGradeOverride`` will ever exist for a given ``PersistentSubsectionGrade``.
  That is, write actions against ``PersistentSubsectionGradeOverride`` are always an update-or-create action,
  using the primary key of the ``PersistentSubsectionGrade`` to perform the ``SELECT ... FOR UPDATE`` query.
