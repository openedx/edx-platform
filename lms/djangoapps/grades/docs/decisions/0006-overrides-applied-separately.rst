Subsection Grade Override History and Refactoring
-------------------------------------------------

For background on persistent subsection grade overrides, see 0004-persistent-grade-overrides_.

.. _0004-persistent-grade-overrides: 0004-persistent-grade-overrides.rst

Status
======

Accepted (January 2019)

Context
=======

We want to maintain the score values in the ``PersistentSubsectionGrade`` table as a
source of truth as it relates to the learner's attempt at an assignment.  This is necessary
when, for instance, we want to see an "audit trail" of manually changed grades via the
Gradebook feature.  We'd like an instructor to see both the original grade as obtained
by the student, as well as all changes made via ``PersistentSubsectionGradeOverrides``.
Therefore, we need to make two changes:

* The existence of a ``PersistentSubsectionGradeOverride`` should no longer change the score values
  of the associated ``PersistentSubsectionGrade``.
* We'll introduce a ``PersistentSubsectionGradeOverrideHistory`` table to track changes to grades
  made via grade overrides.

Decisions
=========

* We'll introduce a ``PersistentSubsectionGradeOverrideHistory`` table.  This table will track
  who created the override, the reason for the change (i.e. due to proctoring failure or a change
  via Gradebook), and any comments made by the overriding user.
* As detailed in this `Jira issue <https://openedx.atlassian.net/browse/EDUCATOR-3835>`_, we'll
  refactor the grades override logic to no longer override the parameters of a ``PersistentSubsectionGrade``
  during updates where an associated ``PersistentSubsectionGradeOverride`` exists.
* The ``SubsectionGrade`` classes should now account for any associated overrides and factor those
  into the subsection- and course-level grades when presenting grade data via a client
  (e.g. Gradebook, instructor grade reports, the Progress page).
