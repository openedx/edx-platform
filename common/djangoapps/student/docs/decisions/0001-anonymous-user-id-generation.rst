Anonymous User Id Generation
--------------

Status
======

Accepted

Context
=======

The student app provides a mechanism to generate multiple anonymous ids for a
student.  The anonymous ID can be independent of all courses or it can be
course specific.  To generate the anonymous ID, we currently hash the user's
``id`` with the Django ``SECRET_KEY`` and a course key if provided.  The
mapping between the anonymous ID and user ``id`` are saved in the
``AnonymousUserID`` table.

As it stands, if the ``SECRET_KEY`` is rotated students would get new anonymous
IDs starting immediately after rotation.  This can cause downstream issues
where the IDs are output from the system.  For example, the IDs are in tracking
data and could be used to track a user's activity through a course for research
purposes.

Decisions
=========

Once an anonymous ID is generated for a user in a particular LearningContext
(either a course or some other unit of learning), it will remain that way even
if the secret used to generate the ID changes.  For any context where an
anonymous ID does not already exist, a new ID will be generated using the
latest ``SECRET_KEY``.


Consequences
============

By keeping old IDs static, we increase the risk that if the salting
data(``SECRET_KEY``) is leaked, then it can be used to determine and correlate
all anonymous IDs associated with a particular user across all courses. We
believe that this is a worth while risk to not break downstream services that
are using anonymous IDs during the lifetime of a course.

Rejected Alternatives
=====================

Make Anonymous IDs Randomly Generated
-------------------------------------

The function that generates anonymous IDs, has the option to not persist the
newly generated ID. In this case, it would give a new anonymous key each time
the function was called, instead of being consistent other than at key
rotation. The downstream consequence of changing the SECRET_KEY that often are
unclear so we opt not to do so at this time. In the future if we can ensure
that the newly generated IDs are always persisted, we could more safely use
random generation.
