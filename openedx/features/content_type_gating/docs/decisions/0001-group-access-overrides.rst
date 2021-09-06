1. Group Access Overrides
=========================

Status
------

Accepted

Context
-------

In order to implement Feature Based Enrollment (FBE), we need to be able
to automatically restrict content to a specific set of authorized
users. This automatic restriction needs to be based on whether content
is graded and capable of producing a score. Whether a particular XBlock
is graded and scorable is denoted by attributes on that XBlock.

There are two separate systems that need load XBlocks and need to
be restricted: the courseware rendering on the web, and the courseware
rendering in the mobile app. Courseware rendering accesses XBlock
attributes via the ``FieldData`` api, and can be modified by
``FieldDataOverrides``. The mobile app uses the course_blocks api,
which is backed by ``BlockTransformers``.

Most differentiated content is managed by ``UserPartitions``. These
segment users by customizable criteria, and then can be applied as
access control by setting the ``group_access`` field on an ``XBlock``.
There is an existing ``UserPartition`` that segments users based on
their enrollment track (the ``EnrollmentTrackUserPartition``. However,
many courses already manage content using the ``EnrollmentTrackUserPartition``,
so it isn't a good candidate to overwrite for FBE.


Decision
--------

In order to restrict access to graded content, we will create a new
``UserPartition`` specifically for FBE. That partition will segment
users based on their enrollment track and any other criteria that become
relevant for FBE implementation. We will override the ``group_access``
of all graded and scorable XBlocks by using a new ``FieldDataOverride``
for in-courseware acccess, and a new ``BlockTransformer`` for mobile/
course_blocks api access. Both of those will respect the same rules for
when to override the ``group_access`` attribute.

Consequences
------------

All graded content (with possible manual exceptions) will have ``group_access``
overridden to assign the content to the "Full Access Only" partition of
the new ``ContentTypeGatingPartition``. Studio Authors will see reference
to both the ``ContentTypeGatingPartition`` (Feature Based Enrollment Partition)
and the ``EnrollmentTrack`` partition in Studio, if they are authorized to
modify them. Masquerade, which only modifies a single group at a time, is
unable to provide an accurate simulation of the interaction between having
graded content restricted behind the ``EnrollmentTrack`` partition.
