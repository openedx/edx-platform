Status: Maintenance

Responsibilities
================
The Student app supplements Django's default user information with student-specific information like User Profiles and Enrollments. This has made it a catch all place for a lot of functionality that we want to move into more dedicated places. For instance, while the CourseEnrollment models remain in this app for now, most Enrollment related functionality has already moved to the Enrollment app.

If you are thinking of adding something here, strongly consider adding a new Django app instead. If you are extending something here, please consider extracting it into a separate app.

Intended responsibility: Student dashboard functionality.

Glossary
========


More Documentation
==================

Plugins
-------
Plugin Context view names (see ADR 0003-plugin-contexts.rst):
* "course_dashboard" -> student.views.dashboard.student_dashboard
