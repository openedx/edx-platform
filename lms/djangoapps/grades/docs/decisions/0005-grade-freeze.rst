Freezing Changes to Subsection and Course Grades
------------------------------------------------

Status
======

Accepted (circa Summer 2018)

Context
=======

We would like to prevent subsection-level and course-level grades from being
updated in a course that has ended, after some fixed period of time.  After that fixed
period of time, we consider grades for that course "frozen" - they can no longer be changed
by the system.  This is important for maintaining the integrity of grades and a learner's completion of a course,
particularly in credit-bearing courses.

Decisions
=========

* In ``lms/djangoapps/grades/tasks.py``, we'll introduce an ``are_grades_frozen`` function
  to determine, for a given course key, whether subsection and course grades should now be
  frozen for that course.
* The fixed period of time after course end at which grades will be frozen is 30 days.
* By default, we'll freeze grades 30 days after the course end date for all courses,
  unless a ``CourseWaffleFlag`` is present for the course. An existing, but *disabled*,
  Waffle flag course override causes grades to not be frozen (after any amount of time)
  for that particular course.
* Any grading celery task that can update grades will now check if grades are frozen
  before taking any action.  If grades for the course are frozen, the task will simply
  return without taking any further action.

Consequences
============

As a consequence of this decision, persistent grades will now be inconsistent with the
values computed from input scores, course content, grading policy, etc. if changes
to any of these occur after the frozen date.
