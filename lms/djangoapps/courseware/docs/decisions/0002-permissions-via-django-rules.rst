0002. Use `django-rules`_ for Permissions and Tracks
****************************************************

~~~~~~~
Context
~~~~~~~

`OEP-9`_ mandates the use of `django-rules`_ to provide a flexible
implementation of permissions in edX applications. `edx-platform`_
predates that OEP, and uses a home-grown API for checking permissions.
That API, `has_access`_, uses predominately role-based checks and
implicit permissions, rather than explicitly named permissions. That is,
`has_access`_ is called to check if a user has a role in a course,
and then a users ability to perform an action is inferred from
that role. As a result, it is difficult to separate the roles in
the edx-platform system from the permissions that are granted to those
roles (or to grant existing permissions to new roles).

Similarly, most permissions relating to student course access are
based on the users enrollment in a particular track, and are checked
by examining the `CourseMode`_ of that enrollment. As a result, adding
new ``CourseModes`` with similar but not identical permissions requires
numerous distributed code changes.

.. _OEP-9: https://open-edx-proposals.readthedocs.io/en/latest/oep-0009-bp-permissions.html
.. _CourseMode: https://github.com/edx/edx-platform/blob/master/common/djangoapps/course_modes/models.py#L37
.. _edx-platform: https://github.com/edx/edx-platform

~~~~~~~~
Decision
~~~~~~~~

We will update all uses of `has_access`_, and all `CourseMode`_ membership
checks, to use `django-rules`_ and named permissions.

Plan of Action
==============

#. Write a subclass of ``Predicate`` to allow for non-booleans to be returned during
   evaluation.
#. Convert built-in predicates to non-boolean predicates in edx-platform.
#. For each caller of ``has_access``:

   #. Convert the caller to use ``user.has_perm`` instead.
   #. Implement the new permission created in 1. by referencing to the previous
      ``has_access`` call.

#. Refactor contents of ``has_access`` out into their own predicates that can
   be used to implement specific permissions.
#. For each place that checks if a user is enrolled in a specific track:

   #. Convert the that check to use ``user.has_perm`` for a named permission
   #. Implement that permission by checking

Details
=======

Subclass ``Predicate``
----------------------

The `Predicate`_ class provided by `django-rules`_ takes some
pains to make sure that the results of predicates are explicitly booleans,
rather than just being objects that are truthy. In order to return objects
like `AccessResponse`_, which may encode additional data about the
particular predicate that failed, we need to modify `Predicate`_.

In particular, we will need to remove two instances of explicit conversion
to boolean:

* https://github.com/dfunckt/django-rules/blob/master/rules/predicates.py#L154
* https://github.com/dfunckt/django-rules/blob/master/rules/predicates.py#L214

There may be other spots that need adjustment as well, to make sure
that we always return the non-boolean predicate results through, given
the option. We also need a policy for what happens if multiple
non-boolean predicates are being combined with ``&`` and ``|``. Until
proven otherwise, my recommendation is that the first such predicate is
returned. We could in the future add functionality to return a list of all
failing predicates.

Additionally, https://github.com/dfunckt/django-rules/blob/master/rules/predicates.py#L183
should convert ``other`` to a non-boolean predicate if it isn't already.
Note, though, that this won't covert a boolean-only predicate to a
non-boolean predicate if the boolean-only predicate is first in the chain.

Finally, we need to make sure that ``__invert__`` doesn't lose error
messages (https://github.com/dfunckt/django-rules/blob/master/rules/predicates.py#L173)

.. _django-rules: https://github.com/dfunckt/django-rules
.. _AccessResponse: https://github.com/edx/edx-platform/blob/master/lms/djangoapps/courseware/access_response.py#L10
.. _Predicate: https://github.com/dfunckt/django-rules/blob/master/rules/predicates.py#L47

Convert built-in predicates to non-boolean predicates in edx-platform
---------------------------------------------------------------------

`django-rules`_ includes a number of built-in predicates related to standard
django permissions. We should make it easy to convert an existing predicate
into a non-boolean response predicate, and provide convenience versions of
the built-in predicates in edx-platform that have already been converted.
However, we could consider doing this work on-demand as we need the built-ins,
rather than up front. The risk is that it would be easy for future developers
to miss the existence of the edx-platform versions if they aren't commonly
in use already in edx-platform.

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

.. _has_access: https://github.com/edx/edx-platform/blob/master/lms/djangoapps/courseware/access.py#L103
.. _user.has_perm: https://docs.djangoproject.com/en/2.1/ref/contrib/auth/#django.contrib.auth.models.User.has_perm

Refactor contents of ``has_access``
-----------------------------------

As implemented, `has_access`_ has many subclauses to handle the various
roles and object types. With `django-rules`_, those clauses could be converted
to smaller individual predicates, either divided by roles, object types,
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

Accepted

~~~~~~~~~~~~
Consequences
~~~~~~~~~~~~

When the conversion of `has_access`_ has been completed, it will be easier
to add additional conditions to various permissions checks on specific objects.
It will also allow those conditions (predicates) to be written in
a location that is central to the app they are responsible for, rather
than requiring that they be added to `access.py`_.

.. _access.py: https://github.com/edx/edx-platform/blob/master/lms/djangoapps/courseware/access.py

When the conversion of `CourseMode`_ membership checks has been completed,
it will be easier to add new `CourseMode`_ types with similar permissions
schema to the codebase. It will also open the way towards making `CourseMode`_
permissions be data-driven, rather than being code specific, which would
allow configuration-time specification of `CourseMode`_, rather than requiring
the current combination of code and database entries.
