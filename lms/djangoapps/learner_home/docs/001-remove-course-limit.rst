Remove course_limit
--------------

Status
======

Approved

Context
=======

In the old student dashboard we had a built-in limit for the number of courses to show on the page (DASHBOARD_COURSE_LIMIT, 250). Previously, the user could manually show all courses by clicking a link on the page, shown only if they were enrolled in more courses than the course limit.

For the new learner dashboard, we need the ability to sort/filter. Without a currently built in way to paginate, we needed a way to either add or remove the issue of partial filters/sorting.

Decisions
=========

To avoid the potential for filtering/sorting being incomplete, for the new dashboard we have decided to remove the dashboard course limit. This means all users will see all of their courses on their homepage by default. This will make local sorting and filtering accurate.

Consequences
============

After taking a, hopefully, representative sample of users (by usage over a certain time period) we identified that ~0.2% of users meet or exceed the current dashboard limit, so we expect the impact to be small.

Possible consequences are longer page load time and increased backend system utilization.


Alternatives
============

1.  We could design a pagination system for querying course enrollments. Unclear the technical lift here.
2.  We could only show up to a set limit and either restrict or, as before, have a manual trigger to request the full list of courses.