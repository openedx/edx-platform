1. Sysadmin Dashboard
---------------------

Status
------

Accepted

Context
-------
When operating an Open edX installation, it is convenient to allow admins and course staff to perform some tasks from
the web browser instead of requiring access to django managment commands. These tasks include

- creating user accounts
- importing courses (from git)
- deleting courses
- gathering cross-course enrollment data

The SysAdmin Dashboard feature has remained functionally unchanged since 2015, but it has never been documented.
This ADR serves to captures the decisions that went into it, so that we may being the process of moving it out of
edx-platofrm and into a pluggable django app.

Decision
--------

The users tab provides Web based user management (create and delete user accounts), a listing of courses loaded,
and user statistics.

The courses tabs manages adding/updating courses from git, deleting courses, and provides course listing information,
including commit hash, date and author for course imported from git.

The Staffing tab provides a view of staffing and enrollment in courses.

The Gitlogs tab provides a view into the import log of courses from git repositories. It is convenient for allowing
course teams to see what may be wrong wit their xml. This is the only view that allows permits access by course
staff, so they can review their own course import logs.

Consequences
------------

The Sysadmin dashboard is little used outside of MIT and difficult to maintain. Many of its features have been
replicated elsewhere in edx-platform. It coudld be refactored as a pluggable app, but some of it's features rely on
internal edX APIs. In a subsequent ADR, we will identify the APIs that would be necessary for extracting the Sysadmin
Dashboard.
