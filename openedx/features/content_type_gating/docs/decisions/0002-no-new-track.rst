2. No New Enrollment Mode
=========================

Status
------

Accepted

Context
-------

In order to implement Feature Based Enrollment (FBE), we need a way
to differentiate between users who have access to graded content
and those who don't. We need to be able to move users between those
groups. Users that have access to graded content should also get
all of the current behavior associated with Verified users. We
need to leave existing users (in any track) with their existing behavior.
Many permissions related to Enrollment Modes are checked by checking
whether an enrollment has a specific mode, which makes it hard
to add a new mode that has the same set of permissions.


Decision
--------

Rather than adding a new Enrollment Track that we move Full-Access users
into, we will add a new ``UserPartition`` to distinguish Limited-Access Users
and Full-Access Users.

Consequences
------------

Some Studio Authors see both the new ``ContentTypeGatingPartition`` and the
``EnrollmentTrackUserPartition`` in their UI. Masquerade is unable to
masquerade as a user in a specific group and see graded content that has
been limited using the ``EnrollemntTrackUserPartition``, because it doesn't
multi-select groups.
