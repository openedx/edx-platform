0003. Use `bridgekeeper`_ for Permissions and Tracks
****************************************************

~~~~~~~
Context
~~~~~~~

In `0002. Use django-rules for Permissions and Tracks`_, the case was
laid out for using `django-rules`_ to manage permissions. In the intervening
time, no active work has been done to complete the conversion. During that
period, authorization checking was observed to be a significant performance
in several list views of courses (the CourseListView from course_api and
the student dashboard view). In both cases, access checking had to be performed
after the CourseOverview had been loaded from the database, and resulted
in significant numbers of additional queries.

`bridgekeeper`_ is a library with an interface that is very similar to
`django-rules`_, except that it also supports specifying the permissions
as Django query filters. By inspection, it seems to support non-boolean
return values for the Python-based permissions checks.

.. _bridgekeeper: https://bridgekeeper.readthedocs.io/en/latest/index.html
.. _django-rules: https://github.com/dfunckt/django-rules

~~~~~~~~
Decision
~~~~~~~~

Rather than use `django-rules`_ in edx-platform, we will convert permissions
checks to use `bridgekeeper`_. The conversion will follow a similar outline
to the plan in `0002`_.

We will update all uses of `has_access`_, and all `CourseMode`_ membership
checks, to use `bridgekeeper`_ and named permissions.

.. _`0002. Use django-rules for Permissions and Tracks`: https://github.com/openedx/edx-platform/blob/master/lms/djangoapps/courseware/docs/decisions/0002-permissions-via-django-rules.rst
.. _`0002`: https://github.com/openedx/edx-platform/blob/master/lms/djangoapps/courseware/docs/decisions/0002-permissions-via-django-rules.rst

Plan of Action
==============

#. For each caller of ``has_access``:

   #. Convert the caller to use ``user.has_perm`` instead.
   #. Implement the new permission created in 1. by referencing to the
      previous ``has_access`` call. These `bridgekeeper`_ rules would implement
      ``query`` to raise an exception when called, and implement ``check``
      to pass through to ``has_access``.

#. Refactor contents of ``has_access`` out into their own predicates that can
   be used to implement specific permissions. Where possible, implement
   ``query``, either manually by specifying a custom rule, or by using
   ``Attribute`` or ``Relation`` from `bridgekeeper`_.

#. For any listing views that are currently checking access as a filter
   after querying the database, improve their performance by using the
   `bridgekeeper`_ permission to filter the queryset instead. If those
   views need to display the existence (but not contents) of the object,
   two separate permissions can be used: the first to limit the query
   to only those objects to be displayed, and the second to check whether
   the user has permissions to view the contents of the object.

#. For each place that checks if a user is enrolled in a specific track:

   #. Convert the that check to use ``user.has_perm`` for a named permission
   #. Implement that permission by checking

Details
=======

Convert callers of `has_access`_ to use `user.has_perm`_
--------------------------------------------------------

Currently, the LMS uses `has_access`_ to check if a given user has a particular
role on a particular object (usually a course or an xblock). From that, it
assumes various permissions. The primary goal of this project is to convert
those implicit permissions into explicit named permissions that are tied
to roles by the use of various predicates.

To bootstrap this process, we can wrap `has_access`_ in named permissions by:

#. Convert each caller of `has_access`_ to use `user.has_perm`_ instead.
#. Implement the new permission created in 1. by referencing to the previous
   `has_access`_ call.

This work can be done incrementally, one call to `has_access`_ at a time,
and can be parallelized. However, at present, there are ~150 calls to
`has_access`_ in edx-platform, so this is not an insignificant amount of
work.

.. _has_access: https://github.com/openedx/edx-platform/blob/master/lms/djangoapps/courseware/access.py#L103
.. _user.has_perm: https://docs.djangoproject.com/en/2.1/ref/contrib/auth/#django.contrib.auth.models.User.has_perm

Refactor contents of ``has_access``
-----------------------------------

As implemented, `has_access`_ has many subclauses to handle the various
roles and object types. With `bridgekeeper`_, those clauses could be converted
to smaller individual Rules, either divided by roles, object types,
or both. These predicates would then be simpler to test and to use in
determining future permissions.

Convert track membership tests to permissions
---------------------------------------------

Future work in the same vein would be to convert current usage of track
membership into `user.has_perm`_ checks. This would allow disaggregation
of edx-platform features and would make it easier to add new tracks
with variations of those features.

Offramps
========

The primary offramp would be suspending the project after converting all
callers of `has_access`_ to use `user.has_perm`_. If we have more time,
then refactoring `has_access`_ would be a definite positive, but not
required. If we are forced to cut scope, then only partially completing
the conversion of `has_access`_ would be an improvement, perhaps with
the addition of deprecation warnings for direct callers to `has_access`_
so that we can track the remaining work with INCR tickets.

~~~~~~
Status
~~~~~~

Proposed

~~~~~~~~~~~~
Consequences
~~~~~~~~~~~~

When the conversion of `has_access`_ has been completed, it will be easier
to add additional conditions to various permissions checks on specific objects.
It will also allow those conditions (predicates) to be written in
a location that is central to the app they are responsible for, rather
than requiring that they be added to `access.py`_.

.. _access.py: https://github.com/openedx/edx-platform/blob/master/lms/djangoapps/courseware/access.py

When the conversion of `CourseMode`_ membership checks has been completed,
it will be easier to add new `CourseMode`_ types with similar permissions
schema to the codebase. It will also open the way towards making `CourseMode`_
permissions be data-driven, rather than being code specific, which would
allow configuration-time specification of `CourseMode`_, rather than requiring
the current combination of code and database entries.

Converting all of these checks to use `bridgekeeper`_ will allow list-view
query performance to be optimized.
