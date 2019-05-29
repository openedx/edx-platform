Status: Maintenance

Responsibilities
================
The course_modes app provides functionality for course run offerings (such as audit, verified, etc). It stores which course-modes are offered for each course-run. It provides django server-side rendered views for users to choose their course modes.

Mapping between users to course-runs are outside the scope of course-modes and instead the responsibility of course-run enrollments.

Direction: Replace
==================
Currently, options for modes are hard-coded and thus not as flexible for our desired needs. In the long-term, we want to replace this implementation with a more flexible alternative.

Glossary
========

More Documentation
==================
